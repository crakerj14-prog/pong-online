"""Empujon: el dash de una pala.

Se dispara con una accion, tiene un tiempo de espera entre usos, y mientras
dura desplaza la pala en X hacia adelante y la trae de vuelta sola. No sabe
nada de la bola: solo mueve `pala.x` y marca `pala.dash_activo` mientras va
de ida, para que quien resuelva las colisiones sepa si un golpe fue
"potenciado".

Copia identica de pong/empujon.py.
"""

import ajustes as cfg


class Empujon:
    def __init__(self, pala, hacia_derecha):
        self.pala = pala
        self.hacia_derecha = hacia_derecha   # True: avanza a la derecha (pala izquierda)
        self.x_base = pala.x
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
        """0 justo usado (o todavia en la animacion), 1 listo de nuevo. Para
        dibujar un indicador de cooldown."""
        if self.listo:
            return 1.0
        if self.cooldown_restante > 0:
            return 1 - self.cooldown_restante / cfg.EMPUJON_COOLDOWN_FRAMES
        return 0.0  # en plena animacion de ida/vuelta; el cooldown ni empezo

    def reiniciar(self):
        self.pala.x = self.x_base
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
            self._colocar(1 - self.avance_restante / cfg.EMPUJON_FRAMES_IDA)
            self.pala.dash_activo = True
            if self.avance_restante == 0:
                self.retorno_restante = cfg.EMPUJON_FRAMES_VUELTA
        elif self.retorno_restante > 0:
            self.pala.dash_activo = False
            self.retorno_restante -= 1
            self._colocar(self.retorno_restante / cfg.EMPUJON_FRAMES_VUELTA)
            if self.retorno_restante == 0:
                self.pala.x = self.x_base
                self.cooldown_restante = cfg.EMPUJON_COOLDOWN_FRAMES
        else:
            self.pala.dash_activo = False

    def _colocar(self, proporcion):
        desplazamiento = cfg.EMPUJON_DISTANCIA * proporcion
        self.pala.x = self.x_base + (desplazamiento if self.hacia_derecha else -desplazamiento)
