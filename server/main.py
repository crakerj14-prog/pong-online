"""Servidor autoritativo de Pong triangular, 3 jugadores.

Un solo proceso hace dos cosas:
  1. Sirve los archivos estaticos del cliente (client/index.html, client.js,
     style.css) por HTTP.
  2. Acepta conexiones WebSocket en /ws, empareja de a tres, y corre el loop
     de juego para cada partida a 60 cuadros por segundo.

El campo es un triangulo: cada jugador defiende un borde. Si se le escapa
la bola por una parte que su pala no cubre, pierde una vida; a las 0 vidas
su borde se convierte en pared fija (sigue rebotando la bola, pero ya no
hay nada que perder ahi). Gana el ultimo jugador con vidas.

Puede haber varias bolas en juego a la vez (poder "multibola") y varios
poderes esperando en el campo al mismo tiempo. Cuando se pierde una vida,
sea cual sea la bola que se escapo, se limpia todo y se vuelve a sacar con
una sola bola -- asi el estado nunca queda a medio camino entre "una bola
menos" y "sigue habiendo dos".

Los clientes nunca calculan fisica: mandan input (teclado, mouse, el
disparo del empujon) y reciben el estado completo en cada cuadro, mas una
lista de "eventos" puntuales para particulas/sonido. Ver PROTOCOLO.md.

Ejecutar con:  uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import math
import random
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

import ajustes as cfg
import colisiones
import colisiones_triangulo
import geometria
from empujon import Empujon
from entidades import Bola
from impulso import Impulso
from pala_triangular import PalaBorde
from poderes import Poderes

RAIZ = Path(__file__).resolve().parent
CLIENTE_DIR = RAIZ.parent / "client"

app = FastAPI()


def _rotar(vx, vy, angulo):
    """Rota el vector (vx, vy) `angulo` radianes."""
    cos_a, sin_a = math.cos(angulo), math.sin(angulo)
    return vx * cos_a - vy * sin_a, vx * sin_a + vy * cos_a


class Jugador:
    """Un extremo de la conexion: el WebSocket y el input que va mandando."""

    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.arriba = False
        self.abajo = False
        self.mouse_x = None
        self.mouse_y = None
        self.modo_control = "teclado"  # o "mouse": gana el que se uso mas reciente
        self.partida = None            # se asigna al emparejar
        self.numero = None             # 1, 2 o 3, se asigna al emparejar

    @property
    def direccion(self):
        """-1 hacia `a`, +1 hacia `b` a lo largo del borde. Mismo signo que
        PalaBorde.mover()."""
        return int(self.abajo) - int(self.arriba)


class Obstaculo:
    """Bloque que rebota solo en un cuadrado central. Se comporta como una
    pala inmovil para colisiones.resolver_pala (mismo truco que en la
    version de 2 jugadores): nadie la controla, nunca le imprime efecto a
    la bola."""

    def __init__(self, x, y, ancho, alto, vx, vy):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto
        self.vx = vx
        self.vy = vy
        self.velocidad_actual = 0.0

    @property
    def centro_y(self):
        return self.y + self.alto / 2

    def caja(self):
        return self.x, self.y, self.x + self.ancho, self.y + self.alto

    def mover(self, x_min, x_max, y_min, y_max):
        self.x += self.vx
        self.y += self.vy
        if self.x < x_min or self.x + self.ancho > x_max:
            self.vx = -self.vx
            self.x = max(x_min, min(x_max - self.ancho, self.x))
        if self.y < y_min or self.y + self.alto > y_max:
            self.vy = -self.vy
            self.y = max(y_min, min(y_max - self.alto, self.y))


def _limites_obstaculos():
    return (
        cfg.CENTRO_X - cfg.OBSTACULO_RADIO_ZONA,
        cfg.CENTRO_X + cfg.OBSTACULO_RADIO_ZONA,
        cfg.CENTRO_Y - cfg.OBSTACULO_RADIO_ZONA,
        cfg.CENTRO_Y + cfg.OBSTACULO_RADIO_ZONA,
    )


def _crear_obstaculos():
    x_min, x_max, y_min, y_max = _limites_obstaculos()
    obstaculos = []
    for _ in range(cfg.OBSTACULO_CANTIDAD):
        x = random.uniform(x_min, x_max - cfg.OBSTACULO_ANCHO)
        y = random.uniform(y_min, y_max - cfg.OBSTACULO_ALTO)
        vx = random.choice((-1, 1)) * random.uniform(cfg.OBSTACULO_VEL_MIN, cfg.OBSTACULO_VEL_MAX)
        vy = random.choice((-1, 1)) * random.uniform(cfg.OBSTACULO_VEL_MIN, cfg.OBSTACULO_VEL_MAX)
        obstaculos.append(Obstaculo(x, y, cfg.OBSTACULO_ANCHO, cfg.OBSTACULO_ALTO, vx, vy))
    return obstaculos


class Partida:
    """Una partida entre 3 jugadores: el estado y el loop de fisica."""

    def __init__(self, jugadores):
        self.jugadores = jugadores  # lista de 3 Jugador, indice 0/1/2 = numero 1/2/3
        self.palas = [PalaBorde(borde) for borde in geometria.BORDES]
        self.bolas = [Bola()]
        self.obstaculos = _crear_obstaculos()
        self.poderes = Poderes(self.palas)
        self.empujones = [Empujon(pala) for pala in self.palas]
        self.impulso = Impulso()
        self.impulso_bola = None  # a cual de self.bolas le esta aplicando el impulso ahora
        self.eventos = []

        self.vidas = [cfg.VIDAS_INICIALES] * 3
        self.eliminado = [False, False, False]
        self.ultimo_en_golpear = None  # numero 1/2/3, o None

        self.espera_saque = 0
        self.terminada = False
        self.ganador = None
        self.activa = True
        self._sacar()

    # --- Ciclo de partida ------------------------------------------------
    def _sacar(self):
        """Deja una sola bola en juego, saliendo del centro en una direccion
        al azar. Se usa tanto al arrancar la partida como despues de
        cualquier vida perdida (incluso si en ese momento habia varias bolas
        por el poder multibola: todas se descartan y se vuelve a esta)."""
        bola = self.bolas[0] if self.bolas else Bola()
        angulo = random.uniform(0, math.tau)
        bola.vx = math.cos(angulo) * cfg.BOLA_VEL_INICIAL
        bola.vy = math.sin(angulo) * cfg.BOLA_VEL_INICIAL
        bola.x = cfg.CENTRO_X - bola.tam / 2
        bola.y = cfg.CENTRO_Y - bola.tam / 2
        bola.x_previo, bola.y_previo = bola.x, bola.y
        self.bolas = [bola]
        self.espera_saque = cfg.FRAMES_SAQUE
        self.impulso.cancelar()
        self.impulso_bola = None
        self.ultimo_en_golpear = None

    def activar_empujon(self, numero_jugador):
        empujon = self.empujones[numero_jugador - 1]
        if empujon.activar():
            self._evento_sonido(200, 40)

    # --- Bucle de fisica ---------------------------------------------------
    def actualizar(self):
        for indice, jugador in enumerate(self.jugadores):
            if self.eliminado[indice]:
                continue
            self._mover_jugador(self.palas[indice], jugador)
            self.palas[indice].actualizar_efecto()
            self.palas[indice].actualizar_paralisis()
            self.empujones[indice].actualizar()

        self.poderes.actualizar_spawn(habilitado=True)

        x_min, x_max, y_min, y_max = _limites_obstaculos()
        for obstaculo in self.obstaculos:
            obstaculo.mover(x_min, x_max, y_min, y_max)

        if self.espera_saque > 0:
            self.espera_saque -= 1
            return

        if self.impulso_bola is not None and self.impulso_bola in self.bolas:
            self.impulso.actualizar(self.impulso_bola)
        elif self.impulso.activo:
            # La bola que tenia el impulso ya no esta en juego (se perdio una
            # vida y se reseteo todo): se cancela prolijo en vez de quedar
            # con un color/temporizador que ya no describe nada real.
            self.impulso.cancelar()
            self.impulso_bola = None

        self._mover_bolas()

    def _mover_jugador(self, pala, jugador):
        """Teclado mueve a velocidad fija; mouse sigue al cursor 1 a 1 salvo
        que este paralizada (ver PalaBorde.mover_a). Nota de riesgo aceptado
        sobre el mouse sin tope de velocidad: un salto de cursor muy rapido
        en teoria podria saltearse la bola sin que se detecte el choque."""
        if jugador.modo_control == "mouse" and jugador.mouse_x is not None:
            s = pala.borde.posicion_tangencial((jugador.mouse_x, jugador.mouse_y))
            pala.mover_a(s)
        else:
            pala.mover(jugador.direccion)

    def _mover_bolas(self):
        for bola in list(self.bolas):
            if bola not in self.bolas:
                continue  # una bola perdida antes en este mismo cuadro ya reseteo todo
            self._mover_una_bola(bola)

    def _mover_una_bola(self, bola):
        bola.x_previo, bola.y_previo = bola.x, bola.y
        bola.x += bola.vx
        bola.y += bola.vy

        for indice, borde in enumerate(geometria.BORDES):
            pala = None if self.eliminado[indice] else self.palas[indice]
            resultado = colisiones_triangulo.procesar_borde(bola, borde, pala, self.eliminado[indice])
            if resultado is None:
                continue

            if resultado["tipo"] == "perdida":
                self._perder_vida(indice)
                return

            color_pala = f"pala{indice + 1}"
            self._evento_particulas(bola.centro_x, bola.centro_y, color_pala, 14)
            self._evento_sonido(int(480 + resultado["rapidez"] * 22), 20)

            if not self.eliminado[indice]:
                self.ultimo_en_golpear = indice + 1
                if self.palas[indice].dash_activo:
                    self.impulso.activar(bola, cfg.IMPULSO_COLOR)
                    self.impulso_bola = bola
                    self._evento_particulas(bola.centro_x, bola.centro_y, cfg.IMPULSO_COLOR, 26)
                    self._evento_sonido(900, 60)
                elif bola is self.impulso_bola:
                    # Golpe normal en la MISMA bola que tenia el impulso: la
                    # fisica normal ya le recalculo la velocidad. Un golpe
                    # normal en OTRA bola no le toca el impulso a esta.
                    self.impulso.cancelar()
                    self.impulso_bola = None
            break
        else:
            for obstaculo in self.obstaculos:
                resultado = colisiones.resolver_pala(bola, obstaculo, cfg.DIFICULTAD)
                if resultado is None:
                    continue
                cantidad = 14 if resultado["tipo"] == "frontal" else 8
                self._evento_particulas(bola.centro_x, bola.centro_y, "acento", cantidad)
                self._evento_sonido(300, 15)
                break

            resultado_poder = self.poderes.recoger_si_toca(bola, self.ultimo_en_golpear)
            if resultado_poder is not None:
                self._evento_particulas(bola.centro_x, bola.centro_y, resultado_poder["color"], 22)
                self._evento_sonido(700, 45)
                self._aplicar_poder_extendido(resultado_poder, bola)

    def _perder_vida(self, indice_jugador):
        self.vidas[indice_jugador] -= 1
        borde = geometria.BORDES[indice_jugador]
        centro_borde = borde.punto(borde.longitud / 2)
        self._evento_particulas(centro_borde[0], centro_borde[1], "acento", 26)
        self._evento_sonido(180, 90)

        if self.vidas[indice_jugador] <= 0:
            self.eliminado[indice_jugador] = True
            self.palas[indice_jugador].offset_normal = 0.0

        vivos = [n for n in range(3) if not self.eliminado[n]]
        if len(vivos) <= 1:
            self.terminada = True
            self.ganador = vivos[0] + 1 if vivos else None
            return

        self._sacar()

    # --- Poderes que necesitan mas que "palas" (los resuelve Poderes) -------
    def _aplicar_poder_extendido(self, info, bola):
        """"crecer"/"encoger"/"veloz"/"lenta" ya los aplico
        Poderes.recoger_si_toca; estos tres necesitan la lista de bolas o de
        empujones, que ese objeto no tiene."""
        if self.ultimo_en_golpear is None:
            return

        if info["tipo"] == "multibola":
            self._crear_bolas_extra(bola)
        elif info["tipo"] == "empujon_libre":
            duracion_frames = int(info["duracion"] * cfg.FPS)
            self.empujones[self.ultimo_en_golpear - 1].activar_sin_cooldown(duracion_frames)
        elif info["tipo"] == "paralisis":
            otros = [n for n in (1, 2, 3) if n != self.ultimo_en_golpear]
            objetivo = random.choice(otros)
            duracion_frames = int(info["duracion"] * cfg.FPS)
            self.palas[objetivo - 1].aplicar_paralisis(cfg.PARALISIS_MULTIPLICADOR, duracion_frames)
            # Ralentiza la bola a la vez: le da una chance real al paralizado
            # en vez de solo dejarlo mirando (ver notas de diseño del poder).
            self._escalar_bola(bola, cfg.PODER_FACTOR_LENTA)

    def _crear_bolas_extra(self, bola_origen):
        libres = cfg.MULTIBOLA_MAX_BOLAS - len(self.bolas)
        cantidad = min(cfg.MULTIBOLA_CANTIDAD_EXTRA, max(0, libres))
        for i in range(cantidad):
            angulo = math.radians(35 + i * 25) * (1 if i % 2 == 0 else -1)
            vx, vy = _rotar(bola_origen.vx, bola_origen.vy, angulo)
            nueva = Bola()
            nueva.x, nueva.y = bola_origen.x, bola_origen.y
            nueva.x_previo, nueva.y_previo = bola_origen.x, bola_origen.y
            nueva.vx, nueva.vy = vx, vy
            self.bolas.append(nueva)

    @staticmethod
    def _escalar_bola(bola, factor):
        actual = bola.velocidad
        if actual == 0:
            return
        nueva = max(cfg.PODER_VEL_MIN, min(cfg.BOLA_VEL_MAX, actual * factor))
        escala = nueva / actual
        bola.vx *= escala
        bola.vy *= escala

    # --- Eventos puntuales (particulas/sonido) ------------------------------
    def _evento_particulas(self, x, y, color, cantidad):
        """`color` es un hex fijo ("#rrggbb") o una clave de tema
        ("pala1"/"pala2"/"pala3"/"acento") que el cliente resuelve contra su
        propia paleta local."""
        self.eventos.append({
            "tipo": "particulas", "x": round(x, 1), "y": round(y, 1),
            "color": color, "cantidad": cantidad,
        })

    def _evento_sonido(self, frecuencia, duracion):
        self.eventos.append({"tipo": "sonido", "frecuencia": frecuencia, "duracion": duracion})

    # --- Serializacion -------------------------------------------------------
    def estado_json(self):
        poderes_json = [
            {
                "tipo": info["tipo"], "simbolo": info["simbolo"], "color": info["color"],
                "x": round(info["x"], 1), "y": round(info["y"], 1),
            }
            for info in self.poderes.activos
        ]

        palas_json = []
        for indice, pala in enumerate(self.palas):
            cx, cy = pala.centro_mundo()
            palas_json.append({
                "x": round(cx, 1), "y": round(cy, 1),
                "largo": round(pala.largo, 1),
                "eliminado": self.eliminado[indice],
            })

        mensaje = {
            "type": "estado",
            "bolas": [{"x": round(b.x, 1), "y": round(b.y, 1)} for b in self.bolas],
            "palas": palas_json,
            "vidas": list(self.vidas),
            "obstaculos": [
                {"x": round(o.x, 1), "y": round(o.y, 1), "ancho": o.ancho, "alto": o.alto}
                for o in self.obstaculos
            ],
            "saque": self.espera_saque > 0,
            "cuenta_saque": self.espera_saque // (cfg.FRAMES_SAQUE // 3 + 1) + 1,
            "terminada": self.terminada,
            "ganador": self.ganador,
            "poderes": poderes_json,
            "empujon": [round(e.proporcion_espera, 2) for e in self.empujones],
            "impulso_color": self.impulso.color,
            "eventos": self.eventos,
        }
        self.eventos = []
        return mensaje


async def bucle_partida(partida: Partida):
    """Tick fijo a cfg.FPS por segundo: fisica + broadcast a los 3 jugadores."""
    intervalo = 1 / cfg.FPS
    while partida.activa:
        partida.actualizar()
        mensaje = partida.estado_json()
        for jugador in partida.jugadores:
            try:
                await jugador.ws.send_json(mensaje)
            except Exception:
                partida.activa = False
        if partida.terminada:
            break
        await asyncio.sleep(intervalo)


# Jugadores esperando para completar un trio. Como mucho 2 en espera: en
# cuanto llega el tercero, se arma la partida y la lista queda vacia.
esperando: list = []
lock_emparejar = asyncio.Lock()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global esperando
    await ws.accept()
    jugador = Jugador(ws)

    async with lock_emparejar:
        esperando.append(jugador)
        if len(esperando) < 3:
            grupo = None
        else:
            grupo = esperando[:3]
            esperando = esperando[3:]

    if grupo is None:
        await ws.send_json({
            "type": "esperando",
            "conectados": len(esperando),
            "necesarios": 3,
        })
    else:
        for indice, j in enumerate(grupo):
            j.numero = indice + 1
        partida = Partida(grupo)
        for j in grupo:
            j.partida = partida

        base_inicio = {
            "campo": {"ancho": cfg.ANCHO, "alto": cfg.ALTO},
            "vertices": [list(v) for v in geometria.VERTICES],
            "bordes": [
                {"a": list(b.a), "b": list(b.b), "angulo": b.angulo}
                for b in geometria.BORDES
            ],
            "pala": {"largo": cfg.PALA_LARGO, "grosor": cfg.PALA_GROSOR},
            "bola": {"tam": cfg.BOLA_TAM},
            "poder_tam": cfg.PODER_TAM,
            "vidas_iniciales": cfg.VIDAS_INICIALES,
        }
        for j in grupo:
            await j.ws.send_json({"type": "inicio", "numero": j.numero, **base_inicio})

        asyncio.create_task(bucle_partida(partida))

    try:
        while True:
            mensaje = await ws.receive_json()
            tipo = mensaje.get("type")
            if tipo == "input":
                tecla = mensaje.get("tecla")
                presionada = bool(mensaje.get("presionada"))
                if tecla == "arriba":
                    jugador.arriba = presionada
                elif tecla == "abajo":
                    jugador.abajo = presionada
                jugador.modo_control = "teclado"
            elif tipo == "mouse":
                x, y = mensaje.get("x"), mensaje.get("y")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    jugador.mouse_x = float(x)
                    jugador.mouse_y = float(y)
                    jugador.modo_control = "mouse"
            elif tipo == "accion":
                if mensaje.get("accion") == "empujon" and jugador.partida is not None:
                    jugador.partida.activar_empujon(jugador.numero)
    except WebSocketDisconnect:
        pass
    finally:
        async with lock_emparejar:
            if jugador in esperando:
                esperando.remove(jugador)

        if jugador.partida is not None:
            jugador.partida.activa = False
            for otro in jugador.partida.jugadores:
                if otro is not jugador:
                    try:
                        await otro.ws.send_json({"type": "rival_desconectado"})
                    except Exception:
                        pass


# Se monta al final: las rutas declaradas arriba (/ws) tienen prioridad sobre
# este catch-all de archivos estaticos.
app.mount("/", StaticFiles(directory=CLIENTE_DIR, html=True), name="cliente")
