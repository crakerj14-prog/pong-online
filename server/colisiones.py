"""Fisica de choque bola-pared y bola-pala.

Copia identica de pong/colisiones.py (el juego de escritorio). No se toco ni
una linea: estas funciones ya eran independientes de tkinter (solo mueven la
bola y devuelven que paso), asi que corren igual dentro del loop del servidor.
"""

import math

import ajustes as cfg
from entidades import solapan


def chocar_con_paredes(bola):
    """Rebota contra techo o suelo si corresponde. Devuelve la Y del choque
    (0 o cfg.ALTO) para poder ubicar las particulas ahi, o None si no choco.
    """
    if bola.y <= 0:
        bola.y = 0
        bola.vy = abs(bola.vy)
        return 0
    if bola.y + bola.tam >= cfg.ALTO:
        bola.y = cfg.ALTO - bola.tam
        bola.vy = -abs(bola.vy)
        return cfg.ALTO
    return None


def resolver_pala(bola, pala, dificultad):
    """Colision bola-pala.

    Primero busca el cruce de la cara frontal durante el frame (barrido),
    porque a alta velocidad la bola puede saltarse la pala entera. Si no hubo
    cruce pero estan solapadas, se expulsa por el lado menos hundido: asi un
    golpe en el canto sale por arriba o por abajo, en vez de teletransportarse
    a la cara frontal.

    Devuelve None si no hubo choque, o un dict {"tipo": "frontal", "rapidez": x}
    / {"tipo": "canto"} con lo necesario para que el llamador elija sonido y
    particulas.
    """
    hacia_derecha = _cruce_frontal(bola, pala)
    if hacia_derecha is not None:
        rapidez = _rebote_frontal(bola, pala, hacia_derecha, dificultad)
        return {"tipo": "frontal", "rapidez": rapidez}

    if not solapan(bola.caja(), pala.caja()):
        return None

    bx1, by1, bx2, by2 = bola.caja()
    px1, py1, px2, py2 = pala.caja()
    penetraciones = (
        (bx2 - px1, "izquierda"),
        (px2 - bx1, "derecha"),
        (by2 - py1, "arriba"),
        (py2 - by1, "abajo"),
    )
    _, lado = min(penetraciones, key=lambda par: par[0])

    if lado == "izquierda":
        rapidez = _rebote_frontal(bola, pala, False, dificultad)
        return {"tipo": "frontal", "rapidez": rapidez}
    if lado == "derecha":
        rapidez = _rebote_frontal(bola, pala, True, dificultad)
        return {"tipo": "frontal", "rapidez": rapidez}

    if lado == "arriba":
        bola.y = py1 - bola.tam
        bola.vy = -abs(bola.vy)
    else:
        bola.y = py2
        bola.vy = abs(bola.vy)
    return {"tipo": "canto"}


def _cruce_frontal(bola, pala):
    """Si la bola cruzo la cara frontal de la pala este frame, hacia donde rebota.

    Devuelve True (sale hacia la derecha), False (hacia la izquierda) o None.
    """
    if bola.vx > 0:                      # llega por la izquierda de la pala
        plano = pala.x - bola.tam
        hacia_derecha = False
    elif bola.vx < 0:                    # llega por la derecha de la pala
        plano = pala.x + pala.ancho
        hacia_derecha = True
    else:
        return None

    if not (min(bola.x_previo, bola.x) <= plano <= max(bola.x_previo, bola.x)):
        return None

    recorrido = bola.x - bola.x_previo
    t = (plano - bola.x_previo) / recorrido if recorrido else 0.0
    y_contacto = bola.y_previo + (bola.y - bola.y_previo) * t
    if y_contacto + bola.tam > pala.y and y_contacto < pala.y + pala.alto:
        # Coloca la bola en el punto real del impacto antes de rebotar, para
        # que el angulo se calcule con la altura correcta.
        bola.y = y_contacto
        return hacia_derecha
    return None


def _rebote_frontal(bola, pala, hacia_derecha, dificultad):
    """El angulo de salida depende del punto de la pala donde pega la bola.
    Devuelve la rapidez objetivo del rebote (antes del efecto de la pala), que
    el llamador usa para escalar el tono del sonido.
    """
    desplazamiento = (bola.centro_y - pala.centro_y) / (pala.alto / 2)
    desplazamiento = max(-1.0, min(1.0, desplazamiento))

    rapidez = min(bola.velocidad * dificultad["aceleracion"], cfg.BOLA_VEL_MAX)
    angulo = desplazamiento * cfg.BOLA_ANGULO_MAX
    bola.vx = rapidez * math.cos(angulo) * (1 if hacia_derecha else -1)
    bola.vy = rapidez * math.sin(angulo)

    # Una pala en movimiento arrastra la bola: da control sobre el rebote.
    bola.vy += pala.velocidad_actual * cfg.EFECTO_PALA
    _normalizar_velocidad(bola, rapidez)

    # Deja la bola justo fuera de la pala, nunca dentro.
    bola.x = pala.x + pala.ancho if hacia_derecha else pala.x - bola.tam
    return rapidez


def _normalizar_velocidad(bola, rapidez_objetivo):
    """Reajusta el vector tras el efecto de la pala, sin perder direccion."""
    actual = bola.velocidad
    if actual == 0:
        return
    factor = min(rapidez_objetivo, cfg.BOLA_VEL_MAX) / actual
    bola.vx *= factor
    bola.vy *= factor

    # Evita que la bola quede rebotando casi en vertical. La rapidez se lee
    # antes de tocar vx, porque si no el reparto se calcularia sobre el vector
    # ya modificado.
    rapidez = bola.velocidad
    minimo = rapidez * cfg.VX_MINIMO
    if abs(bola.vx) < minimo:
        bola.vx = math.copysign(minimo, bola.vx or 1.0)
        sobrante = rapidez ** 2 - bola.vx ** 2
        bola.vy = math.copysign(math.sqrt(max(0.0, sobrante)), bola.vy or 1.0)
