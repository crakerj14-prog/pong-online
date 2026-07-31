"""Constantes de fisica del servidor: 2, 3 o 4 jugadores, elegido por el
anfitrion antes de arrancar (ver Lobby en server/main.py).

El campo siempre vive en un lienzo de ANCHO x ALTO. Segun la cantidad de
jugadores, geometria.construir() arma una forma distinta adentro de ese
lienzo:
  2 -> rectangulo clasico: arriba/abajo son paredes fijas desde el arranque
       (nunca tuvieron pala ni vidas), izquierda/derecha son los jugadores.
  3 -> triangulo equilatero: los 3 lados son de jugador.
  4 -> cuadrado: los 4 lados son de jugador.
El centro del lienzo coincide siempre con el centro de la forma, a
proposito: asi entidades.Bola (que se centra en (ANCHO-tam)/2,
(ALTO-tam)/2) sirve sin tocarle una linea para el saque en el medio.
"""

ANCHO, ALTO = 800, 800
CENTRO_X, CENTRO_Y = ANCHO / 2, ALTO / 2

# Triangulo (3) y cuadrado (4): poligono regular inscripto en un circulo de
# este radio, centrado en (CENTRO_X, CENTRO_Y).
RADIO_POLIGONO = 340

# Rectangulo (2 jugadores): mitades de ancho/alto. La proporcion (680x420)
# se parece a la del Pong de escritorio (800x500).
RECT_MEDIO_ANCHO = 340
RECT_MEDIO_ALTO = 210

FPS = 60

PALA_LARGO = 82   # a lo largo del borde (equivalente a PALA_ALTO del modo 2D)
PALA_GROSOR = 12  # perpendicular al borde (equivalente a PALA_ANCHO)
PALA_VEL = 7.0

BOLA_TAM = 12
BOLA_VEL_INICIAL = 5.0
BOLA_VEL_MAX = 15.0
BOLA_ANGULO_MAX = 1.0  # radianes (~57 grados) al golpear el borde de la pala

EFECTO_PALA = 0.35

ACELERACION = 1.05
DIFICULTAD = {"aceleracion": ACELERACION}  # formato que espera colisiones.resolver_pala (obstaculos)

FRAMES_SAQUE = 55
VIDAS_INICIALES = 3


# --- Poderes -------------------------------------------------------------
# El color de cada poder es fijo (no depende del tema): el cliente lo usa
# tal cual. "peso" es el peso relativo al sortear (mas peso, mas frecuente).
#
# Pueden aparecer varios a la vez en el campo (ver PODER_MAX_SIMULTANEOS):
# cada tanto se intenta generar uno nuevo sin importar si los anteriores
# siguen sin agarrar, hasta llegar al tope.
PODERES = [
    {"tipo": "crecer", "nombre": "Pala grande", "simbolo": "+",
     "color": "#4ade80", "duracion": 7.0, "peso": 3},
    {"tipo": "encoger", "nombre": "Pala rival chica", "simbolo": "-",
     "color": "#f87171", "duracion": 6.0, "peso": 3},
    {"tipo": "veloz", "nombre": "Bola rapida", "simbolo": ">>",
     "color": "#fbbf24", "duracion": 0, "peso": 3},
    {"tipo": "lenta", "nombre": "Bola lenta", "simbolo": "<<",
     "color": "#60a5fa", "duracion": 0, "peso": 1},
    {"tipo": "multibola", "nombre": "Multibola", "simbolo": "x3",
     "color": "#e879f9", "duracion": 0, "peso": 2},
    {"tipo": "empujon_libre", "nombre": "Empujon sin limite", "simbolo": "!!",
     "color": "#fb923c", "duracion": 6.0, "peso": 2},
    {"tipo": "paralisis", "nombre": "Paralisis", "simbolo": "Zz",
     "color": "#818cf8", "duracion": 4.0, "peso": 2},
]

PODER_TAM = 20
PODER_INTERVALO_MIN_SEG = 6
PODER_INTERVALO_MAX_SEG = 11
PODER_MAX_SIMULTANEOS = 4  # tope de poderes esperando en el campo a la vez
PODER_FACTOR_CRECER = 1.6
PODER_FACTOR_ENCOGER = 0.55
PODER_FACTOR_VELOZ = 1.45
PODER_FACTOR_LENTA = 0.6
PODER_VEL_MIN = 3.0
PODER_RADIO_SPAWN = 150  # radio del circulo central donde puede aparecer (cabe en las 3 formas, ver nota de OBSTACULO_RADIO_ZONA)

# Multibola: cuantas bolas extra suma (clonadas de la que la toco, con la
# velocidad rotada un poco para cada lado) y el tope total de bolas en juego.
MULTIBOLA_CANTIDAD_EXTRA = 2
MULTIBOLA_MAX_BOLAS = 3

# Paralisis: no inmoviliza del todo (eso dejaria inutil el enlentecimiento de
# la bola que la acompaña, que es justamente lo que le da una chance al
# paralizado); lo deja moviendose muy despacio.
PARALISIS_MULTIPLICADOR = 0.18


# --- Empujon (dash) ----------------------------------------------------------
EMPUJON_FRAMES_IDA = 7
EMPUJON_FRAMES_VUELTA = 12
EMPUJON_DISTANCIA = 46
EMPUJON_COOLDOWN_SEG = 9
EMPUJON_COOLDOWN_FRAMES = EMPUJON_COOLDOWN_SEG * FPS

# --- Impulso: lo que le pasa a la bola cuando un empujon la golpea ----------
IMPULSO_FACTOR_PICO = 1.55
IMPULSO_TECHO = 1.4
IMPULSO_FACTOR_ASENTADO = 1.30
IMPULSO_DURACION_SEG = 3.0
IMPULSO_COLOR = "#ff3864"


# --- Obstaculos ----------------------------------------------------------
# Bloques que rebotan solos en un cuadrado central. OBSTACULO_RADIO_ZONA=90
# tiene que caber comodo en la forma mas chica de las tres: el rectangulo
# de 2 jugadores, cuya distancia del centro al borde mas cercano
# (arriba/abajo) es RECT_MEDIO_ALTO=210. Le sobra margen de sobra en los
# otros dos modos (el triangulo, el mas ajustado de los poligonos, tiene
# 170 de radio inscripto).
OBSTACULO_CANTIDAD = 2
OBSTACULO_ANCHO = 20
OBSTACULO_ALTO = 60
OBSTACULO_VEL_MIN = 1.2
OBSTACULO_VEL_MAX = 2.4
OBSTACULO_RADIO_ZONA = 90


# --- Lobby -----------------------------------------------------------------
CANTIDADES_JUGADORES_POSIBLES = (2, 3, 4)
