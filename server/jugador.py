"""Un jugador conectado: el WebSocket y el input que va mandando.

No sabe nada de fisica ni de reglas -- eso es trabajo de Partida. Solo
guarda el ultimo estado de teclado/mouse que mando el cliente, para que
Partida lo lea en cada cuadro.
"""

from fastapi import WebSocket


class Jugador:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.arriba = False
        self.abajo = False
        self.mouse_x = None
        self.mouse_y = None
        self.modo_control = "teclado"  # o "mouse": gana el que se uso mas reciente
        self.partida = None            # se asigna al arrancar la partida (ver lobby.py)
        self.numero = None             # 1..4, se asigna al arrancar (protocolo: 1-based)

    @property
    def direccion(self):
        """-1 hacia `a`, +1 hacia `b` a lo largo del borde. Mismo signo que
        PalaBorde.mover()."""
        return int(self.abajo) - int(self.arriba)
