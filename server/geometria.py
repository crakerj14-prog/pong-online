"""Geometria del campo: se arma distinto segun la cantidad de jugadores,
pero siempre como una lista de `Borde` (uno por cada lado de la forma).

Para 3 y 4 jugadores, la forma es un poligono regular (triangulo, cuadrado)
donde CADA lado es de un jugador. Para 2, la forma es un rectangulo donde
SOLO 2 de los 4 lados son de jugador (izquierda/derecha); arriba/abajo
quedan sin dueño desde el arranque -- Partida los trata igual que un lado
cuyo jugador ya fue eliminado: rebotan siempre, nunca hacen perder una vida.
Eso es lo que unifica los 3 modos con la misma fisica de colision (ver
colisiones_triangulo.py, que en realidad no es especifico de triangulos):
un borde con pala asignada puede hacer perder una vida si la bola pasa por
donde la pala no llega; un borde sin pala asignada es siempre pared.

`construir(cantidad_jugadores)` devuelve (vertices, bordes, mapeo), donde
`mapeo` es {indice_jugador (0-based): indice_borde}. Cualquier indice de
borde que no aparezca en `mapeo.values()` es una pared fija de entrada.
"""

import math
import random

import ajustes as cfg


class Borde:
    """Un lado de la forma, de `a` a `b`."""

    def __init__(self, a, b):
        self.a = a
        self.b = b
        dx, dy = b[0] - a[0], b[1] - a[1]
        self.longitud = math.hypot(dx, dy)
        self.tangente = (dx / self.longitud, dy / self.longitud)
        # Hacia adentro de la forma. Verificado a mano contra el centroide
        # para el triangulo y el cuadrado (misma regla, forma generica);
        # para el rectangulo se armo directamente para que de bien (ver
        # _vertices_rectangulo).
        self.normal = (-self.tangente[1], self.tangente[0])
        self.angulo = math.atan2(dy, dx)

    def punto(self, s):
        """Punto sobre el borde a distancia `s` (a lo largo) del extremo `a`."""
        return (self.a[0] + self.tangente[0] * s, self.a[1] + self.tangente[1] * s)

    def distancia_normal(self, punto):
        """Distancia con signo de `punto` a la recta del borde, medida hacia
        adentro de la forma (positiva = del lado de adentro)."""
        return (punto[0] - self.a[0]) * self.normal[0] + (punto[1] - self.a[1]) * self.normal[1]

    def posicion_tangencial(self, punto):
        """A que distancia de `a`, a lo largo del borde, cae la proyeccion
        de `punto` (puede dar fuera de [0, longitud] si el punto no esta
        realmente enfrente del borde)."""
        return (punto[0] - self.a[0]) * self.tangente[0] + (punto[1] - self.a[1]) * self.tangente[1]


def _vertice_poligono(indice, cantidad_lados):
    angulo = math.radians(-90 + indice * (360 / cantidad_lados))
    return (
        cfg.CENTRO_X + cfg.RADIO_POLIGONO * math.cos(angulo),
        cfg.CENTRO_Y + cfg.RADIO_POLIGONO * math.sin(angulo),
    )


def _vertices_rectangulo():
    cx, cy = cfg.CENTRO_X, cfg.CENTRO_Y
    ma, mh = cfg.RECT_MEDIO_ANCHO, cfg.RECT_MEDIO_ALTO
    # Sentido horario en pantalla (Y para abajo), igual que el poligono
    # regular: arriba-izq -> arriba-der -> abajo-der -> abajo-izq.
    return [
        (cx - ma, cy - mh),
        (cx + ma, cy - mh),
        (cx + ma, cy + mh),
        (cx - ma, cy + mh),
    ]


def construir(cantidad_jugadores):
    """Arma la forma para `cantidad_jugadores` (2, 3 o 4).

    Devuelve (vertices, bordes, mapeo). `mapeo` es {indice_jugador: indice_borde}.
    """
    if cantidad_jugadores == 2:
        vertices = _vertices_rectangulo()
        # bordes: 0=arriba, 1=derecha, 2=abajo, 3=izquierda (ver el orden de
        # _vertices_rectangulo). Arriba/abajo quedan afuera del mapeo: son
        # paredes fijas desde el arranque, igual que en el Pong clasico.
        mapeo = {0: 3, 1: 1}  # jugador 0 (el "1" de cara al jugador) = izquierda, jugador 1 = derecha
    else:
        vertices = [_vertice_poligono(i, cantidad_jugadores) for i in range(cantidad_jugadores)]
        mapeo = {i: i for i in range(cantidad_jugadores)}

    bordes = [
        Borde(vertices[i], vertices[(i + 1) % len(vertices)])
        for i in range(len(vertices))
    ]
    return vertices, bordes, mapeo


def punto_aleatorio_central(radio):
    """Punto uniforme dentro de un circulo de `radio` centrado en el medio
    del campo (coincide con el centro de cualquiera de las 3 formas)."""
    angulo = random.uniform(0, math.tau)
    r = radio * math.sqrt(random.random())
    return (cfg.CENTRO_X + r * math.cos(angulo), cfg.CENTRO_Y + r * math.sin(angulo))
