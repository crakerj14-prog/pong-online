"""Impulso: el golpe extra que deja un empujon (dash) al conectar con la bola.

Sube la velocidad de golpe por encima del limite normal, marca que la bola
deberia cambiar de color durante unos segundos, y despues se asienta en un
nivel mas alto que el normal en vez de volver del todo a como estaba.

Copia identica de pong/impulso.py.
"""

import ajustes as cfg


class Impulso:
    def __init__(self):
        self.frames_restantes = 0
        self.velocidad_asentada = 0.0
        self.color = None

    @property
    def activo(self):
        return self.frames_restantes > 0

    def cancelar(self):
        """Se usa cuando la bola recibe un golpe normal: la fisica normal ya le
        recalculo la velocidad, asi que el color/temporizador del impulso
        anterior quedaria mintiendo si se dejara puesto."""
        self.frames_restantes = 0
        self.color = None

    def activar(self, bola, color):
        """Se llama justo despues de resolver un golpe que ya traia la
        velocidad normal del rebote (con la dificultad ya aplicada); esto le
        agrega el pico del impulso y programa el asentamiento a los 3s.
        """
        velocidad_base = bola.velocidad
        if velocidad_base == 0:
            return
        objetivo = min(
            velocidad_base * cfg.IMPULSO_FACTOR_PICO,
            cfg.BOLA_VEL_MAX * cfg.IMPULSO_TECHO,
        )
        self._escalar(bola, objetivo)

        self.velocidad_asentada = velocidad_base * cfg.IMPULSO_FACTOR_ASENTADO
        self.frames_restantes = int(cfg.IMPULSO_DURACION_SEG * cfg.FPS)
        self.color = color

    def actualizar(self, bola):
        if self.frames_restantes <= 0:
            return
        self.frames_restantes -= 1
        if self.frames_restantes == 0:
            self._escalar(bola, self.velocidad_asentada)
            self.color = None

    @staticmethod
    def _escalar(bola, objetivo):
        actual = bola.velocidad
        if actual == 0:
            return
        factor = objetivo / actual
        bola.vx *= factor
        bola.vy *= factor
