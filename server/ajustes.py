"""Constantes de fisica del servidor.

Usa los mismos nombres que pong/ajustes.py (el juego de escritorio) para
poder copiar entidades.py y colisiones.py sin tocarles una linea: son la
misma fisica, solo que corriendo en el servidor en vez de en un Canvas de
tkinter.

No hay dificultad seleccionable ni CPU aca: son siempre dos humanos, asi que
solo hace falta un unico valor de aceleracion (equivalente al nivel "Normal"
del juego de escritorio).
"""

ANCHO, ALTO = 800, 500
FPS = 60

PALA_ANCHO, PALA_ALTO = 12, 82
PALA_VEL = 7.0
PALA_MARGEN = 34

BOLA_TAM = 12
BOLA_VEL_INICIAL = 5.0
BOLA_VEL_MAX = 15.0
BOLA_ANGULO_MAX = 1.0  # radianes (~57 grados) al golpear el borde de la pala

EFECTO_PALA = 0.35
VX_MINIMO = 0.30

ACELERACION = 1.05  # multiplicador de velocidad en cada golpe
DIFICULTAD = {"aceleracion": ACELERACION}  # el formato que espera colisiones.resolver_pala

FRAMES_SAQUE = 55  # cuenta atras antes de cada saque, a FPS cuadros por segundo
PUNTOS_PARA_GANAR = 7


# --- Poderes -------------------------------------------------------------
# Mismos valores que pong/ajustes.py. El color de cada poder es fijo (no
# depende del tema): el cliente lo usa tal cual, sin resolverlo contra su
# paleta local.
PODERES = [
    {"tipo": "crecer", "nombre": "Pala grande", "simbolo": "+",
     "color": "#4ade80", "duracion": 7.0, "peso": 3},
    {"tipo": "encoger", "nombre": "Pala rival chica", "simbolo": "-",
     "color": "#f87171", "duracion": 6.0, "peso": 3},
    {"tipo": "veloz", "nombre": "Bola rapida", "simbolo": ">>",
     "color": "#fbbf24", "duracion": 0, "peso": 3},
    {"tipo": "lenta", "nombre": "Bola lenta", "simbolo": "<<",
     "color": "#60a5fa", "duracion": 0, "peso": 1},
]

PODER_TAM = 20
PODER_INTERVALO_MIN_SEG = 6
PODER_INTERVALO_MAX_SEG = 11
PODER_FACTOR_CRECER = 1.6
PODER_FACTOR_ENCOGER = 0.55
PODER_FACTOR_VELOZ = 1.45
PODER_FACTOR_LENTA = 0.6
PODER_VEL_MIN = 3.0
PODER_ZONA_X = (0.30, 0.70)
PODER_MARGEN_Y = 40


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
IMPULSO_COLOR = "#ff3864"  # fijo, no depende del tema del cliente


# --- Obstaculos ----------------------------------------------------------
# Bloques que rebotan solos en la franja central, lejos de ambas palas.
# OBSTACULO_ZONA_X los confina como fraccion del ancho del campo: con
# margen 34 + ancho de pala 12 = 46, y la zona empezando en 0.36 (=288px),
# queda de sobra sin invadir donde se mueven las palas.
OBSTACULO_CANTIDAD = 2
OBSTACULO_ANCHO = 20
OBSTACULO_ALTO = 60
OBSTACULO_VEL_MIN = 1.2
OBSTACULO_VEL_MAX = 2.4
OBSTACULO_ZONA_X = (0.36, 0.64)
