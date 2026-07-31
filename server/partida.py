"""El estado y la fisica de una partida en curso, entre 2, 3 o 4 jugadores.

El campo cambia de forma segun la cantidad de jugadores (ver geometria.py):
rectangulo clasico para 2 (arriba/abajo son paredes fijas desde el
arranque), triangulo para 3, cuadrado para 4. En los tres casos, cada
jugador defiende un lado; si se le escapa la bola por una parte que su pala
no cubre, pierde una vida, y a las 0 su lado se convierte en pared fija
(sigue rebotando la bola, pero ya no hay nada que perder ahi). Gana el
ultimo jugador con vidas. Poderes, empujon/impulso, obstaculos y multibola
funcionan igual en los tres modos: son todos parte de la misma fisica
generica de "bola contra un borde con o sin pala asignada".

Puede haber varias bolas en juego a la vez (poder "multibola") y varios
poderes esperando en el campo al mismo tiempo. Cuando se pierde una vida,
sea cual sea la bola que se escapo, se limpia todo y se vuelve a sacar con
una sola bola.
"""

import asyncio
import math
import random

import ajustes as cfg
import colisiones
import colisiones_triangulo
import geometria
import obstaculos
from empujon import Empujon
from entidades import Bola
from impulso import Impulso
from pala_triangular import PalaBorde
from poderes import Poderes


def _rotar(vx, vy, angulo):
    """Rota el vector (vx, vy) `angulo` radianes."""
    cos_a, sin_a = math.cos(angulo), math.sin(angulo)
    return vx * cos_a - vy * sin_a, vx * sin_a + vy * cos_a


def _otro_jugador_al_azar(cantidad_jugadores, menos_este):
    otros = [n for n in range(cantidad_jugadores) if n != menos_este]
    return random.choice(otros)


class Partida:
    """Una partida entre 2, 3 o 4 jugadores: el estado y el loop de fisica.

    Distingue "indice de borde" (0..cantidad_de_lados-1, donde
    cantidad_de_lados puede ser mayor a la cantidad de jugadores: el
    rectangulo de 2 jugadores tiene 4 lados) de "indice de jugador"
    (0-based, 0..cantidad_jugadores-1). `self.palas` y `self.jugador_de_borde`
    estan indexados por borde; casi todo lo demas (vidas, eliminado,
    palas_jugador, empujones_jugador) esta indexado por jugador.
    """

    def __init__(self, jugadores):
        self.jugadores = jugadores
        cantidad = len(jugadores)
        self.vertices, self.bordes, self.mapeo_jugador_a_borde = geometria.construir(cantidad)

        total_bordes = len(self.bordes)
        self.palas = [None] * total_bordes            # indexado por borde; None = pared fija de entrada
        self.jugador_de_borde = [None] * total_bordes  # indice de borde -> indice de jugador, o None

        for indice_jugador, indice_borde in self.mapeo_jugador_a_borde.items():
            self.palas[indice_borde] = PalaBorde(self.bordes[indice_borde])
            self.jugador_de_borde[indice_borde] = indice_jugador

        # Vistas indexadas por jugador, para todo lo que piensa "por
        # jugador" en vez de "por borde" (Poderes, empujones, vidas...).
        self.palas_jugador = [self.palas[self.mapeo_jugador_a_borde[i]] for i in range(cantidad)]

        self.bolas = [Bola()]
        self.obstaculos = obstaculos.crear()
        self.poderes = Poderes(self.palas_jugador)
        self.empujones_jugador = [Empujon(pala) for pala in self.palas_jugador]
        self.impulso = Impulso()
        self.impulso_bola = None  # a cual de self.bolas le esta aplicando el impulso ahora
        self.eventos = []

        self.vidas = [cfg.VIDAS_INICIALES] * cantidad
        self.eliminado = [False] * cantidad
        self.indice_ultimo_en_golpear = None  # indice de jugador (0-based), o None

        self.espera_saque = 0
        self.terminada = False
        self.ganador = None
        self.activa = True  # se apaga cuando alguien se desconecta
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
        self.indice_ultimo_en_golpear = None

    def activar_empujon(self, indice_jugador):
        empujon = self.empujones_jugador[indice_jugador]
        if empujon.activar():
            self._evento_sonido(200, 40)

    # --- Bucle de fisica ---------------------------------------------------
    def actualizar(self):
        for indice_jugador, jugador in enumerate(self.jugadores):
            if self.eliminado[indice_jugador]:
                continue
            pala = self.palas_jugador[indice_jugador]
            self._mover_jugador(pala, jugador)
            pala.actualizar_efecto()
            pala.actualizar_paralisis()
            self.empujones_jugador[indice_jugador].actualizar()

        self.poderes.actualizar_spawn(habilitado=True)

        x_min, x_max, y_min, y_max = obstaculos.limites()
        for obstaculo in self.obstaculos:
            obstaculo.mover(x_min, x_max, y_min, y_max)

        if self.espera_saque > 0:
            self.espera_saque -= 1
            return

        if self.impulso_bola is not None and self.impulso_bola in self.bolas:
            self.impulso.actualizar(self.impulso_bola)
        elif self.impulso.activo:
            # La bola que tenia el impulso ya no esta en juego (se perdio una
            # vida y se reseteo todo): se cancela prolijo.
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

        for indice_borde, borde in enumerate(self.bordes):
            indice_jugador = self.jugador_de_borde[indice_borde]
            # Pared fija: o nunca tuvo jugador (arriba/abajo del rectangulo
            # de 2), o el jugador dueño ya fue eliminado.
            es_pared_fija = indice_jugador is None or self.eliminado[indice_jugador]
            pala = None if es_pared_fija else self.palas[indice_borde]

            resultado = colisiones_triangulo.procesar_borde(bola, borde, pala, es_pared_fija)
            if resultado is None:
                continue

            if resultado["tipo"] == "perdida":
                self._perder_vida(indice_jugador)
                return

            color_pala = f"pala{indice_jugador + 1}" if indice_jugador is not None else "bola"
            self._evento_particulas(bola.centro_x, bola.centro_y, color_pala, 14)
            self._evento_sonido(int(480 + resultado["rapidez"] * 22), 20)

            if indice_jugador is not None and not self.eliminado[indice_jugador]:
                self.indice_ultimo_en_golpear = indice_jugador
                pala_golpeada = self.palas[indice_borde]
                if pala_golpeada.dash_activo:
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

            resultado_poder = self.poderes.recoger_si_toca(bola, self.indice_ultimo_en_golpear)
            if resultado_poder is not None:
                self._evento_particulas(bola.centro_x, bola.centro_y, resultado_poder["color"], 22)
                self._evento_sonido(700, 45)
                self._aplicar_poder_extendido(resultado_poder, bola)

    def _perder_vida(self, indice_jugador):
        self.vidas[indice_jugador] -= 1
        indice_borde = self.mapeo_jugador_a_borde[indice_jugador]
        borde = self.bordes[indice_borde]
        centro_borde = borde.punto(borde.longitud / 2)
        self._evento_particulas(centro_borde[0], centro_borde[1], "acento", 26)
        self._evento_sonido(180, 90)

        if self.vidas[indice_jugador] <= 0:
            self.eliminado[indice_jugador] = True
            self.palas[indice_borde].offset_normal = 0.0

        vivos = [n for n in range(len(self.jugadores)) if not self.eliminado[n]]
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
        if self.indice_ultimo_en_golpear is None:
            return
        indice = self.indice_ultimo_en_golpear

        if info["tipo"] == "multibola":
            self._crear_bolas_extra(bola)
        elif info["tipo"] == "empujon_libre":
            duracion_frames = int(info["duracion"] * cfg.FPS)
            self.empujones_jugador[indice].activar_sin_cooldown(duracion_frames)
        elif info["tipo"] == "paralisis":
            objetivo = _otro_jugador_al_azar(len(self.jugadores), indice)
            duracion_frames = int(info["duracion"] * cfg.FPS)
            self.palas_jugador[objetivo].aplicar_paralisis(cfg.PARALISIS_MULTIPLICADOR, duracion_frames)
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
        ("pala1".."pala4", "bola", "acento") que el cliente resuelve contra
        su propia paleta local."""
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
        for indice_jugador in range(len(self.jugadores)):
            pala = self.palas_jugador[indice_jugador]
            cx, cy = pala.centro_mundo()
            palas_json.append({
                "x": round(cx, 1), "y": round(cy, 1),
                "largo": round(pala.largo, 1),
                "eliminado": self.eliminado[indice_jugador],
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
            "empujon": [round(e.proporcion_espera, 2) for e in self.empujones_jugador],
            "impulso_color": self.impulso.color,
            "eventos": self.eventos,
        }
        self.eventos = []
        return mensaje


async def bucle_partida(partida: Partida):
    """Tick fijo a cfg.FPS por segundo: fisica + broadcast a todos los jugadores."""
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
