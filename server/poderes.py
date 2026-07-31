"""Poderes: icono flotante que aparece cada tanto y modifica la partida al
tocarlo. Con 3 palas no se puede inferir "quien la toco por ultima vez" del
signo de la velocidad (como hacia la version de 2 jugadores): el llamador
tiene que pasarlo explicitamente.
"""

import random

import ajustes as cfg
import geometria


class Poderes:
    def __init__(self, palas):
        self.palas = palas  # lista de 3 PalaBorde, indice 0/1/2 = jugador 1/2/3
        self.actual = None
        self.frames_restantes = self._nuevo_intervalo()

    def reiniciar(self):
        self.actual = None
        self.frames_restantes = self._nuevo_intervalo()

    def _nuevo_intervalo(self):
        return random.randint(
            cfg.PODER_INTERVALO_MIN_SEG * cfg.FPS, cfg.PODER_INTERVALO_MAX_SEG * cfg.FPS
        )

    def actualizar_spawn(self, habilitado):
        if not habilitado:
            self.actual = None
            return
        if self.actual is not None:
            return
        self.frames_restantes -= 1
        if self.frames_restantes <= 0:
            self._generar()

    def _generar(self):
        pesos = [p["peso"] for p in cfg.PODERES]
        info = dict(random.choices(cfg.PODERES, weights=pesos, k=1)[0])
        x, y = geometria.punto_aleatorio_central(cfg.PODER_RADIO_SPAWN)
        info["x"], info["y"] = x, y
        self.actual = info

    def caja(self):
        x, y, r = self.actual["x"], self.actual["y"], cfg.PODER_TAM / 2
        return x - r, y - r, x + r, y + r

    def recoger_si_toca(self, bola, ultimo_en_golpear):
        """`ultimo_en_golpear` es el numero (1, 2 o 3) de quien toco la bola
        por ultima vez, o None si nadie la toco todavia en esta jugada."""
        if self.actual is None:
            return None

        x1, y1, x2, y2 = self.caja()
        bx1, by1, bx2, by2 = bola.caja()
        if not (bx1 < x2 and bx2 > x1 and by1 < y2 and by2 > y1):
            return None

        info = self.actual
        self.actual = None
        self.frames_restantes = self._nuevo_intervalo()

        if ultimo_en_golpear is None:
            return info  # se consume el poder pero, sin dueño, no hace nada

        duracion_frames = int(info["duracion"] * cfg.FPS)
        if info["tipo"] == "crecer":
            self.palas[ultimo_en_golpear - 1].aplicar_efecto(cfg.PODER_FACTOR_CRECER, duracion_frames)
        elif info["tipo"] == "encoger":
            otros = [n for n in (1, 2, 3) if n != ultimo_en_golpear]
            objetivo = random.choice(otros)
            self.palas[objetivo - 1].aplicar_efecto(cfg.PODER_FACTOR_ENCOGER, duracion_frames)
        elif info["tipo"] == "veloz":
            self._escalar_bola(bola, cfg.PODER_FACTOR_VELOZ)
        elif info["tipo"] == "lenta":
            self._escalar_bola(bola, cfg.PODER_FACTOR_LENTA)

        return info

    @staticmethod
    def _escalar_bola(bola, factor):
        actual = bola.velocidad
        if actual == 0:
            return
        nueva = max(cfg.PODER_VEL_MIN, min(cfg.BOLA_VEL_MAX, actual * factor))
        escala = nueva / actual
        bola.vx *= escala
        bola.vy *= escala
