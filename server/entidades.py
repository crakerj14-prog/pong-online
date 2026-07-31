"""La bola: la unica entidad geometria-agnostica que se mueve en el campo.

Las palas viven en pala_triangular.py (PalaBorde), parametrizadas por su
borde -- este modulo solo tiene la fisica que no depende para nada de la
forma del campo: la bola y el chequeo de solape entre dos cajas.
"""

import math

import ajustes as cfg


class Bola:
    def __init__(self):
        self.tam = cfg.BOLA_TAM
        self.x = (cfg.ANCHO - self.tam) / 2
        self.y = (cfg.ALTO - self.tam) / 2
        self.x_previo = self.x
        self.y_previo = self.y
        self.vx = 0.0
        self.vy = 0.0

    @property
    def velocidad(self):
        return math.hypot(self.vx, self.vy)

    @property
    def centro_x(self):
        return self.x + self.tam / 2

    @property
    def centro_y(self):
        return self.y + self.tam / 2

    def caja(self):
        return self.x, self.y, self.x + self.tam, self.y + self.tam


def solapan(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1
