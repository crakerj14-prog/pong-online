"""Geometria fija del campo triangular: vertices, bordes (con su normal y
tangente), y puntos aleatorios seguros dentro del triangulo para poderes.

Los 3 vertices se generan a -90, 30 y 150 grados (asi el primero queda
apuntando derecho para arriba). Los bordes se arman recorriendo los
vertices en orden V0->V1->V2->V0; el jugador N controla el borde N (0
indexado internamente, 1/2/3 de cara al protocolo).

Los vertices en ese orden quedan en sentido horario en pantalla (Y para
abajo), asi que la normal "hacia adentro" de cada borde sale de rotar su
tangente 90 grados así: normal = (-tangente.y, tangente.x). Esto se
verifico a mano contra el centroide para los 3 bordes antes de escribir el
codigo (ver notas de diseño).
"""

import math
import random

import ajustes as cfg


def _vertice(indice):
    angulo = math.radians(-90 + indice * 120)
    return (
        cfg.CENTRO_X + cfg.RADIO_TRIANGULO * math.cos(angulo),
        cfg.CENTRO_Y + cfg.RADIO_TRIANGULO * math.sin(angulo),
    )


VERTICES = [_vertice(0), _vertice(1), _vertice(2)]


class Borde:
    """Un lado del triangulo, de `a` a `b`."""

    def __init__(self, a, b):
        self.a = a
        self.b = b
        dx, dy = b[0] - a[0], b[1] - a[1]
        self.longitud = math.hypot(dx, dy)
        self.tangente = (dx / self.longitud, dy / self.longitud)
        self.normal = (-self.tangente[1], self.tangente[0])  # hacia adentro, ver docstring del modulo
        self.angulo = math.atan2(dy, dx)

    def punto(self, s):
        """Punto sobre el borde a distancia `s` (a lo largo) del extremo `a`."""
        return (self.a[0] + self.tangente[0] * s, self.a[1] + self.tangente[1] * s)

    def distancia_normal(self, punto):
        """Distancia con signo de `punto` a la recta del borde, medida hacia
        adentro del triangulo (positiva = del lado de adentro)."""
        return (punto[0] - self.a[0]) * self.normal[0] + (punto[1] - self.a[1]) * self.normal[1]

    def posicion_tangencial(self, punto):
        """A que distancia de `a`, a lo largo del borde, cae la proyeccion
        de `punto` (puede dar fuera de [0, longitud] si el punto no esta
        realmente enfrente del borde)."""
        return (punto[0] - self.a[0]) * self.tangente[0] + (punto[1] - self.a[1]) * self.tangente[1]


BORDES = [
    Borde(VERTICES[0], VERTICES[1]),
    Borde(VERTICES[1], VERTICES[2]),
    Borde(VERTICES[2], VERTICES[0]),
]


def punto_aleatorio_central(radio):
    """Punto uniforme dentro de un circulo de `radio` centrado en el
    centroide del triangulo (coincide con el centro del campo)."""
    angulo = random.uniform(0, math.tau)
    r = radio * math.sqrt(random.random())
    return (cfg.CENTRO_X + r * math.cos(angulo), cfg.CENTRO_Y + r * math.sin(angulo))
