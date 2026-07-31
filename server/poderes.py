"""Poderes: iconos flotantes que aparecen cada tanto y modifican la partida
al tocarlos. Pueden convivir varios en el campo a la vez (hasta
PODER_MAX_SIMULTANEOS): el temporizador de aparicion se reprograma solo cada
vez que expira, sin importar si el anterior se agarro o no.

No se puede inferir "quien la toco por ultima vez" de la velocidad de la
bola (eso solo funcionaba con exactamente 2 palas, una a cada lado): el
llamador tiene que pasarlo explicitamente. Los indices de jugador son
0-based en todo este modulo (jugador 0 es el "jugador 1" de cara al
protocolo, etc), para que coincidan directo con listas como `palas`.

Este modulo resuelve el efecto de "crecer"/"encoger"/"veloz"/"lenta" (solo
necesitan las palas). "multibola"/"empujon_libre"/"paralisis" necesitan
cosas que este objeto no tiene (la lista de bolas, los empujones): se
devuelven en el info para que Partida (en main.py) las termine de aplicar.
"""

import random

import ajustes as cfg
import geometria


class Poderes:
    def __init__(self, palas_por_jugador):
        self.palas = palas_por_jugador  # lista indexada por jugador (0-based)
        self.cantidad_jugadores = len(palas_por_jugador)
        self.activos = []  # poderes esperando en el campo (puede haber varios)
        self.frames_restantes = self._nuevo_intervalo()

    def reiniciar(self):
        self.activos = []
        self.frames_restantes = self._nuevo_intervalo()

    def _nuevo_intervalo(self):
        return random.randint(
            cfg.PODER_INTERVALO_MIN_SEG * cfg.FPS, cfg.PODER_INTERVALO_MAX_SEG * cfg.FPS
        )

    def actualizar_spawn(self, habilitado):
        if not habilitado:
            self.activos = []
            return
        if len(self.activos) >= cfg.PODER_MAX_SIMULTANEOS:
            return
        self.frames_restantes -= 1
        if self.frames_restantes <= 0:
            self._generar()
            # Se reprograma de una: el siguiente poder aparece en su propio
            # intervalo sin importar si este se agarra o no.
            self.frames_restantes = self._nuevo_intervalo()

    def _generar(self):
        pesos = [p["peso"] for p in cfg.PODERES]
        info = dict(random.choices(cfg.PODERES, weights=pesos, k=1)[0])
        x, y = geometria.punto_aleatorio_central(cfg.PODER_RADIO_SPAWN)
        info["x"], info["y"] = x, y
        self.activos.append(info)

    @staticmethod
    def _caja(info):
        x, y, r = info["x"], info["y"], cfg.PODER_TAM / 2
        return x - r, y - r, x + r, y + r

    def recoger_si_toca(self, bola, indice_ultimo_en_golpear):
        """`indice_ultimo_en_golpear` es el indice (0-based) de quien toco la
        bola por ultima vez, o None si nadie la toco todavia en esta jugada.

        A lo sumo agarra un poder por cuadro por bola, para no darle dos
        efectos de golpe si llegaran a superponerse."""
        bx1, by1, bx2, by2 = bola.caja()
        for info in self.activos:
            x1, y1, x2, y2 = self._caja(info)
            if not (bx1 < x2 and bx2 > x1 and by1 < y2 and by2 > y1):
                continue

            self.activos.remove(info)

            if indice_ultimo_en_golpear is not None:
                duracion_frames = int(info["duracion"] * cfg.FPS)
                if info["tipo"] == "crecer":
                    self.palas[indice_ultimo_en_golpear].aplicar_efecto(cfg.PODER_FACTOR_CRECER, duracion_frames)
                elif info["tipo"] == "encoger":
                    objetivo = self._otro_jugador_al_azar(indice_ultimo_en_golpear)
                    self.palas[objetivo].aplicar_efecto(cfg.PODER_FACTOR_ENCOGER, duracion_frames)
                elif info["tipo"] == "veloz":
                    self._escalar_bola(bola, cfg.PODER_FACTOR_VELOZ)
                elif info["tipo"] == "lenta":
                    self._escalar_bola(bola, cfg.PODER_FACTOR_LENTA)
                # "multibola" / "empujon_libre" / "paralisis": los resuelve
                # Partida, que es quien tiene la lista de bolas y empujones.

            return info

        return None

    def _otro_jugador_al_azar(self, menos_este):
        otros = [n for n in range(self.cantidad_jugadores) if n != menos_este]
        return random.choice(otros)

    @staticmethod
    def _escalar_bola(bola, factor):
        actual = bola.velocidad
        if actual == 0:
            return
        nueva = max(cfg.PODER_VEL_MIN, min(cfg.BOLA_VEL_MAX, actual * factor))
        escala = nueva / actual
        bola.vx *= escala
        bola.vy *= escala
