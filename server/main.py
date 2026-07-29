"""Servidor autoritativo de Pong multijugador.

Un solo proceso hace dos cosas:
  1. Sirve los archivos estaticos del cliente (client/index.html, client.js,
     style.css) por HTTP.
  2. Acepta conexiones WebSocket en /ws, empareja de a dos, y corre el loop
     de juego para cada partida a 60 cuadros por segundo.

Los clientes nunca calculan fisica: solo mandan input (teclado, mouse, el
disparo del empujon) y reciben el estado completo del juego en cada cuadro,
mas una lista de "eventos" puntuales (golpes, puntos, poderes) para que
decidan como festejarlos con particulas y sonido. Ver PROTOCOLO.md para el
formato exacto de los mensajes.

Ejecutar con:  uvicorn main:app --reload
"""

from __future__ import annotations  # para poder anotar "Jugador | None" en Python < 3.10

import asyncio
import random
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

import ajustes as cfg
import colisiones
from empujon import Empujon
from entidades import Bola, Pala
from impulso import Impulso
from poderes import Poderes

RAIZ = Path(__file__).resolve().parent
CLIENTE_DIR = RAIZ.parent / "client"

app = FastAPI()


class Jugador:
    """Un extremo de la conexion: el WebSocket y el input que va mandando."""

    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.arriba = False
        self.abajo = False
        self.mouse_y = None       # ultimo Y de mouse recibido, o None si nunca mando uno
        self.modo_control = "teclado"  # o "mouse": gana el que se uso mas reciente
        self.partida = None       # se asigna al emparejar con un rival
        self.numero = None        # 1 o 2, se asigna al emparejar

    @property
    def direccion(self):
        """-1 arriba, +1 abajo, 0 quieto. Mismo signo que Pala.mover()."""
        return int(self.abajo) - int(self.arriba)


class Obstaculo:
    """Bloque que rebota solo en la franja central del campo.

    Se comporta como una pala inmovil para la fisica de rebote — reusa
    colisiones.resolver_pala tal cual, sin tocarle una linea a ese modulo —
    pero nadie la controla y nunca le imprime efecto extra a la bola
    (velocidad_actual siempre en 0).
    """

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


def _crear_obstaculos():
    x_min_frac, x_max_frac = cfg.OBSTACULO_ZONA_X
    x_min = cfg.ANCHO * x_min_frac
    x_max = cfg.ANCHO * x_max_frac
    obstaculos = []
    for _ in range(cfg.OBSTACULO_CANTIDAD):
        x = random.uniform(x_min, x_max - cfg.OBSTACULO_ANCHO)
        y = random.uniform(0, cfg.ALTO - cfg.OBSTACULO_ALTO)
        vx = random.choice((-1, 1)) * random.uniform(cfg.OBSTACULO_VEL_MIN, cfg.OBSTACULO_VEL_MAX)
        vy = random.choice((-1, 1)) * random.uniform(cfg.OBSTACULO_VEL_MIN, cfg.OBSTACULO_VEL_MAX)
        obstaculos.append(Obstaculo(x, y, cfg.OBSTACULO_ANCHO, cfg.OBSTACULO_ALTO, vx, vy))
    return obstaculos


class Partida:
    """Una partida entre dos jugadores: el estado y el loop de fisica."""

    def __init__(self, jugador1: Jugador, jugador2: Jugador):
        self.j1 = jugador1
        self.j2 = jugador2
        self.pala1 = Pala(cfg.PALA_MARGEN)
        self.pala2 = Pala(cfg.ANCHO - cfg.PALA_MARGEN - cfg.PALA_ANCHO)
        self.bola = Bola()
        self.obstaculos = _crear_obstaculos()
        self.poderes = Poderes(self.pala1, self.pala2)
        self.empujon1 = Empujon(self.pala1, hacia_derecha=True)
        self.empujon2 = Empujon(self.pala2, hacia_derecha=False)
        self.impulso = Impulso()
        self.eventos = []  # particulas/sonidos puntuales acumulados desde el ultimo broadcast

        self.marcador = [0, 0]
        self.espera_saque = 0
        self.terminada = False
        self.ganador = None
        self.activa = True  # se apaga cuando alguien se desconecta
        self._sacar(direccion=random.choice((-1, 1)))

    # --- Ciclo de partida ------------------------------------------------
    def _sacar(self, direccion):
        self.bola.reiniciar(direccion, cfg.BOLA_VEL_INICIAL)
        self.espera_saque = cfg.FRAMES_SAQUE
        self.impulso.cancelar()

    def activar_empujon(self, numero_jugador):
        empujon = self.empujon1 if numero_jugador == 1 else self.empujon2
        if empujon.activar():
            self._evento_sonido(200, 40)

    # --- Bucle de fisica ---------------------------------------------------
    def actualizar(self):
        self._mover_jugador(self.pala1, self.j1)
        self._mover_jugador(self.pala2, self.j2)
        self.pala1.actualizar_efecto()
        self.pala2.actualizar_efecto()
        self.empujon1.actualizar()
        self.empujon2.actualizar()
        self.poderes.actualizar_spawn(habilitado=True)

        x_min_frac, x_max_frac = cfg.OBSTACULO_ZONA_X
        x_min, x_max = cfg.ANCHO * x_min_frac, cfg.ANCHO * x_max_frac
        for obstaculo in self.obstaculos:
            obstaculo.mover(x_min, x_max, 0, cfg.ALTO)

        if self.espera_saque > 0:
            self.espera_saque -= 1
            return

        self.impulso.actualizar(self.bola)
        self._mover_bola()

    def _mover_jugador(self, pala, jugador):
        """Teclado mueve a velocidad fija (Pala.mover); mouse sigue al cursor
        1 a 1, sin tope de velocidad — gana el que se uso mas reciente.

        Nota: sin tope de velocidad, en teoria un salto de mouse MUY rapido
        podria saltearse la pelota sin que se detecte el choque (el barrido
        de colisiones.py cubre el movimiento de la pelota, no el de la pala
        saltando de golpe). Para un juego casual el riesgo se acepta: en el
        peor caso se escapa un punto, no se rompe nada. Si algun dia se
        siente injusto, la forma mas simple de arreglarlo es limitar el
        salto maximo por cuadro en _mover_pala_a a algo <= pala.alto.
        """
        if jugador.modo_control == "mouse" and jugador.mouse_y is not None:
            self._mover_pala_a(pala, jugador.mouse_y)
        else:
            pala.mover(jugador.direccion)

    @staticmethod
    def _mover_pala_a(pala, y_centro_objetivo):
        anterior = pala.y
        nueva_y = y_centro_objetivo - pala.alto / 2
        pala.y = max(0, min(cfg.ALTO - pala.alto, nueva_y))
        # Se calcula a mano porque Pala.mover() no se llamo: sin esto, el
        # empujon que la pala le da a la pelota al golpearla (ver
        # colisiones._rebote_frontal) se quedaria con un valor viejo.
        pala.velocidad_actual = pala.y - anterior

    def _mover_bola(self):
        bola = self.bola
        bola.x_previo, bola.y_previo = bola.x, bola.y
        bola.x += bola.vx
        bola.y += bola.vy

        y_pared = colisiones.chocar_con_paredes(bola)
        if y_pared is not None:
            self._evento_particulas(bola.centro_x, y_pared, "bola", 10)
            self._evento_sonido(320, 18)

        for pala in (self.pala1, self.pala2):
            resultado = colisiones.resolver_pala(bola, pala, cfg.DIFICULTAD)
            if resultado is None:
                continue

            color_pala = "pala1" if pala is self.pala1 else "pala2"
            if resultado["tipo"] == "frontal":
                self._evento_particulas(bola.centro_x, bola.centro_y, color_pala, 14)
                self._evento_sonido(int(480 + resultado["rapidez"] * 22), 20)
            else:
                self._evento_particulas(bola.centro_x, bola.centro_y, color_pala, 8)
                self._evento_sonido(260, 16)

            if pala.dash_activo:
                self.impulso.activar(bola, cfg.IMPULSO_COLOR)
                self._evento_particulas(bola.centro_x, bola.centro_y, cfg.IMPULSO_COLOR, 26)
                self._evento_sonido(900, 60)
            else:
                self.impulso.cancelar()
            break

        for obstaculo in self.obstaculos:
            resultado = colisiones.resolver_pala(bola, obstaculo, cfg.DIFICULTAD)
            if resultado is None:
                continue
            cantidad = 14 if resultado["tipo"] == "frontal" else 8
            self._evento_particulas(bola.centro_x, bola.centro_y, "acento", cantidad)
            self._evento_sonido(300, 15)
            break

        resultado_poder = self.poderes.recoger_si_toca(bola)
        if resultado_poder is not None:
            self._evento_particulas(bola.centro_x, bola.centro_y, resultado_poder["color"], 22)
            self._evento_sonido(700, 45)

        if bola.x + bola.tam < 0:
            self._anotar(jugador=2)
        elif bola.x > cfg.ANCHO:
            self._anotar(jugador=1)

    def _anotar(self, jugador):
        indice = jugador - 1
        self.marcador[indice] += 1
        borde = 0 if jugador == 2 else cfg.ANCHO
        self._evento_particulas(borde, self.bola.centro_y, "acento", 26)
        self._evento_sonido(180, 90)

        if self.marcador[indice] >= cfg.PUNTOS_PARA_GANAR:
            self.terminada = True
            self.ganador = jugador
            return
        # Saca hacia quien acaba de encajar el punto.
        self._sacar(direccion=1 if jugador == 1 else -1)

    # --- Eventos puntuales (particulas/sonido) ------------------------------
    def _evento_particulas(self, x, y, color, cantidad):
        """`color` es un hex fijo ("#rrggbb") o una clave de tema
        ("pala1"/"pala2"/"bola"/"acento") que el cliente resuelve contra su
        propia paleta. El servidor no sabe ni le importa que tema tiene
        elegido cada jugador."""
        self.eventos.append({
            "tipo": "particulas", "x": round(x, 1), "y": round(y, 1),
            "color": color, "cantidad": cantidad,
        })

    def _evento_sonido(self, frecuencia, duracion):
        self.eventos.append({"tipo": "sonido", "frecuencia": frecuencia, "duracion": duracion})

    # --- Serializacion -------------------------------------------------------
    def estado_json(self):
        poder = None
        if self.poderes.actual is not None:
            info = self.poderes.actual
            poder = {
                "tipo": info["tipo"], "simbolo": info["simbolo"], "color": info["color"],
                "x": round(info["x"], 1), "y": round(info["y"], 1),
            }

        mensaje = {
            "type": "estado",
            "bola": {"x": round(self.bola.x, 1), "y": round(self.bola.y, 1)},
            "pala1": {"x": round(self.pala1.x, 1), "y": round(self.pala1.y, 1), "alto": round(self.pala1.alto, 1)},
            "pala2": {"x": round(self.pala2.x, 1), "y": round(self.pala2.y, 1), "alto": round(self.pala2.alto, 1)},
            "obstaculos": [
                {"x": round(o.x, 1), "y": round(o.y, 1), "ancho": o.ancho, "alto": o.alto}
                for o in self.obstaculos
            ],
            "marcador": self.marcador,
            "saque": self.espera_saque > 0,
            "cuenta_saque": self.espera_saque // (cfg.FRAMES_SAQUE // 3 + 1) + 1,
            "terminada": self.terminada,
            "ganador": self.ganador,
            "poder": poder,
            "empujon1": round(self.empujon1.proporcion_espera, 2),
            "empujon2": round(self.empujon2.proporcion_espera, 2),
            "impulso_color": self.impulso.color,
            "eventos": self.eventos,
        }
        self.eventos = []
        return mensaje


async def bucle_partida(partida: Partida):
    """Tick fijo a cfg.FPS por segundo: fisica + broadcast a ambos jugadores."""
    intervalo = 1 / cfg.FPS
    while partida.activa:
        partida.actualizar()
        mensaje = partida.estado_json()
        for jugador in (partida.j1, partida.j2):
            try:
                await jugador.ws.send_json(mensaje)
            except Exception:
                # El otro lado ya se entera por su propio receive_json() al
                # desconectarse; aca solo evitamos que un envio fallido tumbe
                # el loop entero.
                partida.activa = False
        if partida.terminada:
            break
        await asyncio.sleep(intervalo)


# Jugador esperando rival. None si no hay nadie en espera. Solo puede haber
# uno a la vez: en cuanto llega un segundo, se emparejan y arranca la partida.
esperando: Jugador | None = None
lock_emparejar = asyncio.Lock()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global esperando
    await ws.accept()
    jugador = Jugador(ws)

    async with lock_emparejar:
        if esperando is None:
            esperando = jugador
            companero = None
        else:
            companero = esperando
            esperando = None

    if companero is None:
        await ws.send_json({"type": "esperando"})
    else:
        companero.numero = 1
        jugador.numero = 2
        partida = Partida(companero, jugador)
        companero.partida = partida
        jugador.partida = partida

        campo = {
            "campo": {"ancho": cfg.ANCHO, "alto": cfg.ALTO},
            "pala": {"ancho": cfg.PALA_ANCHO, "alto": cfg.PALA_ALTO, "margen": cfg.PALA_MARGEN},
            "bola": {"tam": cfg.BOLA_TAM},
            "poder_tam": cfg.PODER_TAM,
            "puntos_para_ganar": cfg.PUNTOS_PARA_GANAR,
        }
        await companero.ws.send_json({"type": "inicio", "numero": 1, **campo})
        await ws.send_json({"type": "inicio", "numero": 2, **campo})

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
                y = mensaje.get("y")
                if isinstance(y, (int, float)):
                    jugador.mouse_y = float(y)
                    jugador.modo_control = "mouse"
            elif tipo == "accion":
                if mensaje.get("accion") == "empujon" and jugador.partida is not None:
                    jugador.partida.activar_empujon(jugador.numero)
    except WebSocketDisconnect:
        pass
    finally:
        async with lock_emparejar:
            if esperando is jugador:
                esperando = None

        if jugador.partida is not None:
            jugador.partida.activa = False
            rival = jugador.partida.j1 if jugador is jugador.partida.j2 else jugador.partida.j2
            try:
                await rival.ws.send_json({"type": "rival_desconectado"})
            except Exception:
                pass


# Se monta al final: las rutas declaradas arriba (/ws) tienen prioridad sobre
# este catch-all de archivos estaticos.
app.mount("/", StaticFiles(directory=CLIENTE_DIR, html=True), name="cliente")
