"""Empujon: el dash de una pala en modo triangular.

Avanza hacia adentro del campo -- a lo largo de la normal de su borde -- y
vuelve sola. A diferencia del modo de 2 jugadores (donde la direccion era
"izquierda" o "derecha"), aca alcanza con un solo numero (`offset_normal`
en PalaBorde) porque la normal de cada borde ya apunta hacia adentro por
definicion: no hace falta un booleano de direccion.
"""

import ajustes as cfg


class Empujon:
    def __init__(self, pala):
        self.pala = pala
        self.cooldown_restante = 0
        self.avance_restante = 0
        self.retorno_restante = 0

    @property
    def listo(self):
        return (self.cooldown_restante <= 0
                and self.avance_restante == 0
                and self.retorno_restante == 0)

    @property
    def proporcion_espera(self):
        """0 justo usado (o todavia en la animacion), 1 listo de nuevo."""
        if self.listo:
            return 1.0
        if self.cooldown_restante > 0:
            return 1 - self.cooldown_restante / cfg.EMPUJON_COOLDOWN_FRAMES
        return 0.0

    def reiniciar(self):
        self.pala.offset_normal = 0.0
        self.pala.dash_activo = False
        self.cooldown_restante = 0
        self.avance_restante = 0
        self.retorno_restante = 0

    def activar(self):
        """Intenta disparar el dash. Devuelve True si arranco de verdad."""
        if not self.listo:
            return False
        self.avance_restante = cfg.EMPUJON_FRAMES_IDA
        return True

    def actualizar(self):
        if self.cooldown_restante > 0:
            self.cooldown_restante -= 1

        if self.avance_restante > 0:
            self.avance_restante -= 1
            proporcion = 1 - self.avance_restante / cfg.EMPUJON_FRAMES_IDA
            self.pala.offset_normal = cfg.EMPUJON_DISTANCIA * proporcion
            self.pala.dash_activo = True
            if self.avance_restante == 0:
                self.retorno_restante = cfg.EMPUJON_FRAMES_VUELTA
        elif self.retorno_restante > 0:
            self.pala.dash_activo = False
            self.retorno_restante -= 1
            proporcion = self.retorno_restante / cfg.EMPUJON_FRAMES_VUELTA
            self.pala.offset_normal = cfg.EMPUJON_DISTANCIA * proporcion
            if self.retorno_restante == 0:
                self.pala.offset_normal = 0.0
                self.cooldown_restante = cfg.EMPUJON_COOLDOWN_FRAMES
        else:
            self.pala.dash_activo = False
