"""Las dos cosas que se mueven en el campo: la pala y la bola.

Copia identica de pong/entidades.py (el juego de escritorio). No se toco ni
una linea: es la misma fisica corriendo en el servidor.
"""

import math
import random

import ajustes as cfg


class Pala:
    def __init__(self, x):
        self.x = x
        self.ancho = cfg.PALA_ANCHO
        self.alto_base = cfg.PALA_ALTO
        self.alto = self.alto_base
        self.velocidad_actual = 0.0
        self.efecto_restante = 0
        self.dash_activo = False    # True mientras un Empujon la tiene lanzada hacia adelante
        self.centrar()

    def centrar(self):
        self.alto = self.alto_base
        self.efecto_restante = 0
        self.y = (cfg.ALTO - self.alto) / 2
        self.velocidad_actual = 0.0
        self.dash_activo = False

    def mover(self, direccion, velocidad=cfg.PALA_VEL):
        """direccion: -1 arriba, +1 abajo, 0 quieto."""
        anterior = self.y
        self.y += direccion * velocidad
        self.y = max(0, min(cfg.ALTO - self.alto, self.y))
        # Se guarda el desplazamiento real para poder darle efecto a la bola.
        self.velocidad_actual = self.y - anterior

    def aplicar_efecto(self, factor, duracion_frames):
        """Crece o encoge la pala manteniendo el mismo centro."""
        centro = self.centro_y
        self.alto = self.alto_base * factor
        self.y = max(0, min(cfg.ALTO - self.alto, centro - self.alto / 2))
        self.efecto_restante = duracion_frames

    def actualizar_efecto(self):
        """Cuenta atras del efecto activo; al terminar vuelve al tamano normal."""
        if self.efecto_restante <= 0:
            return
        self.efecto_restante -= 1
        if self.efecto_restante == 0:
            centro = self.centro_y
            self.alto = self.alto_base
            self.y = max(0, min(cfg.ALTO - self.alto, centro - self.alto / 2))

    @property
    def centro_y(self):
        return self.y + self.alto / 2

    def caja(self):
        return self.x, self.y, self.x + self.ancho, self.y + self.alto


class Bola:
    def __init__(self):
        self.tam = cfg.BOLA_TAM
        self.x = (cfg.ANCHO - self.tam) / 2
        self.y = (cfg.ALTO - self.tam) / 2
        self.x_previo = self.x
        self.y_previo = self.y
        self.vx = 0.0
        self.vy = 0.0

    def reiniciar(self, direccion, velocidad):
        self.x = (cfg.ANCHO - self.tam) / 2
        self.y = (cfg.ALTO - self.tam) / 2
        self.x_previo = self.x
        self.y_previo = self.y
        # Angulo de saque contenido para que no salga casi vertical.
        angulo = random.uniform(-0.42, 0.42)
        self.vx = direccion * velocidad * math.cos(angulo)
        self.vy = velocidad * math.sin(angulo)

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
