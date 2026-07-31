"""Constantes de fisica del servidor: modo triangular, 3 jugadores.

El campo es un cuadrado de ANCHO x ALTO con un triangulo equilatero
inscripto (RADIO_TRIANGULO = distancia del centro a cada vertice). El
centro del cuadrado coincide con el centroide del triangulo a proposito:
asi entidades.Bola (que se centra en (ANCHO-tam)/2, (ALTO-tam)/2) sirve sin
tocarle una linea para el saque en el medio del campo.
"""

ANCHO, ALTO = 800, 800
CENTRO_X, CENTRO_Y = ANCHO / 2, ALTO / 2
RADIO_TRIANGULO = 340

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
# Mismos valores que la version de 2 jugadores. El color de cada poder es
# fijo (no depende del tema): el cliente lo usa tal cual.
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
PODER_RADIO_SPAWN = 150  # radio del circulo central (seguro: cabe en el triangulo) donde puede aparecer


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
# Bloques que rebotan solos en un cuadrado central. El radio del inscripto
# del triangulo (circulo mas grande que cabe adentro) es RADIO_TRIANGULO/2
# = 170 para uno equilatero; OBSTACULO_RADIO_ZONA=90 deja bastante margen
# de sobra para que el cuadrado de rebote nunca toque ningun borde.
OBSTACULO_CANTIDAD = 2
OBSTACULO_ANCHO = 20
OBSTACULO_ALTO = 60
OBSTACULO_VEL_MIN = 1.2
OBSTACULO_VEL_MAX = 2.4
OBSTACULO_RADIO_ZONA = 90
