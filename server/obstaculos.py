"""Bloques que rebotan solos en un cuadrado central del campo, sin dueño y
sin efecto sobre la bola mas alla del rebote fisico.

`Obstaculo` duck-tipea la misma interfaz que colisiones.resolver_pala espera
de una pala (`x`, `y`, `ancho`, `alto`, `caja()`, `centro_y`,
`velocidad_actual`), asi que la fisica de choque bola-obstaculo es la misma
funcion que resuelve bola-pala en el modo de escritorio.
"""

import random

import ajustes as cfg


class Obstaculo:
    def __init__(self, x, y, ancho, alto, vx, vy):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto
        self.vx = vx
        self.vy = vy
        self.velocidad_actual = 0.0  # nunca cambia: nadie la controla, no le da efecto a la bola

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


def limites():
    return (
        cfg.CENTRO_X - cfg.OBSTACULO_RADIO_ZONA,
        cfg.CENTRO_X + cfg.OBSTACULO_RADIO_ZONA,
        cfg.CENTRO_Y - cfg.OBSTACULO_RADIO_ZONA,
        cfg.CENTRO_Y + cfg.OBSTACULO_RADIO_ZONA,
    )


def crear():
    x_min, x_max, y_min, y_max = limites()
    obstaculos = []
    for _ in range(cfg.OBSTACULO_CANTIDAD):
        x = random.uniform(x_min, x_max - cfg.OBSTACULO_ANCHO)
        y = random.uniform(y_min, y_max - cfg.OBSTACULO_ALTO)
        vx = random.choice((-1, 1)) * random.uniform(cfg.OBSTACULO_VEL_MIN, cfg.OBSTACULO_VEL_MAX)
        vy = random.choice((-1, 1)) * random.uniform(cfg.OBSTACULO_VEL_MIN, cfg.OBSTACULO_VEL_MAX)
        obstaculos.append(Obstaculo(x, y, cfg.OBSTACULO_ANCHO, cfg.OBSTACULO_ALTO, vx, vy))
    return obstaculos
