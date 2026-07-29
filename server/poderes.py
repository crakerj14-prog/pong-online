"""Poderes: icono flotante que aparece cada tanto y modifica la partida al
tocarlo. No sabe nada de tkinter ni de sonido: aplica el efecto y devuelve la
info del poder para que quien lo llame decida como celebrarlo (particulas,
pitido, etc).

Copia identica de pong/poderes.py.
"""

import random

import ajustes as cfg
from entidades import solapan


class Poderes:
    def __init__(self, pala_izq, pala_der):
        self.pala_izq = pala_izq
        self.pala_der = pala_der
        self.actual = None                       # poder esperando en el campo, o None
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
        x_min, x_max = cfg.PODER_ZONA_X
        info["x"] = random.uniform(cfg.ANCHO * x_min, cfg.ANCHO * x_max)
        info["y"] = random.uniform(cfg.PODER_MARGEN_Y, cfg.ALTO - cfg.PODER_MARGEN_Y)
        self.actual = info

    def caja(self):
        x, y, r = self.actual["x"], self.actual["y"], cfg.PODER_TAM / 2
        return x - r, y - r, x + r, y + r

    def recoger_si_toca(self, bola):
        """Si la bola toca el poder activo, lo aplica y devuelve su info (para
        que el llamador dispare particulas/sonido). Si no hay contacto, None.
        """
        if self.actual is None or not solapan(bola.caja(), self.caja()):
            return None

        info = self.actual
        self.actual = None
        self.frames_restantes = self._nuevo_intervalo()

        # No hay un registro de "quien golpeo por ultimo": el signo de la
        # velocidad horizontal ya nos dice lo mismo, porque tras cualquier
        # rebote en una pala la bola siempre sale apuntando hacia la otra.
        dueño = "izq" if bola.vx > 0 else "der"
        duracion_frames = int(info["duracion"] * cfg.FPS)

        if info["tipo"] == "crecer":
            pala = self.pala_izq if dueño == "izq" else self.pala_der
            pala.aplicar_efecto(cfg.PODER_FACTOR_CRECER, duracion_frames)
        elif info["tipo"] == "encoger":
            rival = self.pala_der if dueño == "izq" else self.pala_izq
            rival.aplicar_efecto(cfg.PODER_FACTOR_ENCOGER, duracion_frames)
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
