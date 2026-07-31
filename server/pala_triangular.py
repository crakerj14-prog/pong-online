"""La pala de un jugador en el modo triangular.

Vive sobre un borde fijo del campo. Su posicion tiene dos componentes:
  s             -- que tan lejos esta del extremo `a` del borde, a lo largo
                    de el (equivalente al Y de la pala en el modo de 2).
  offset_normal -- que tanto se adelanto hacia adentro del campo (lo mueve
                    el empujon; en reposo es 0, la pala vive justo sobre el
                    borde).
"""

import ajustes as cfg


class PalaBorde:
    def __init__(self, borde):
        self.borde = borde
        self.largo_base = cfg.PALA_LARGO
        self.largo = self.largo_base
        self.s = borde.longitud / 2  # centrada en el borde al arrancar
        self.offset_normal = 0.0
        self.velocidad_actual = 0.0  # ds/dt del ultimo movimiento, para el efecto en la bola
        self.efecto_restante = 0
        self.dash_activo = False

    def centrar(self):
        self.largo = self.largo_base
        self.efecto_restante = 0
        self.s = self.borde.longitud / 2
        self.offset_normal = 0.0
        self.velocidad_actual = 0.0
        self.dash_activo = False

    def _clamped(self, s):
        mitad = self.largo / 2
        return max(mitad, min(self.borde.longitud - mitad, s))

    def mover(self, direccion, velocidad=cfg.PALA_VEL):
        anterior = self.s
        self.s = self._clamped(self.s + direccion * velocidad)
        self.velocidad_actual = self.s - anterior

    def mover_a(self, s_objetivo):
        """Sigue directo al objetivo, sin tope de velocidad (control por mouse)."""
        anterior = self.s
        self.s = self._clamped(s_objetivo)
        self.velocidad_actual = self.s - anterior

    def aplicar_efecto(self, factor, duracion_frames):
        centro = self.s
        self.largo = self.largo_base * factor
        self.s = self._clamped(centro)
        self.efecto_restante = duracion_frames

    def actualizar_efecto(self):
        if self.efecto_restante <= 0:
            return
        self.efecto_restante -= 1
        if self.efecto_restante == 0:
            centro = self.s
            self.largo = self.largo_base
            self.s = self._clamped(centro)

    def centro_mundo(self):
        """Posicion (x, y) del centro de la pala, con el offset del empujon incluido."""
        px, py = self.borde.punto(self.s)
        nx, ny = self.borde.normal
        return (px + nx * self.offset_normal, py + ny * self.offset_normal)

    def rango_s(self):
        """(s_min, s_max) que cubre la pala sobre el borde, para el choque."""
        mitad = self.largo / 2
        return self.s - mitad, self.s + mitad
