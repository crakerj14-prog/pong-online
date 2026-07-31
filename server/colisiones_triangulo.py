"""Fisica de choque bola-borde para el campo triangular.

Cada borde puede estar en dos estados: activo (un jugador con vidas lo
defiende con su pala) o pared fija (el jugador de ese borde ya fue
eliminado). En los dos casos la bola rebota igual; la diferencia es que en
un borde activo, si la bola cruza por una parte que la pala no cubre,
cuenta como vida perdida en vez de rebotar.

El rebote se calcula en la base local del borde (normal = hacia adentro del
campo, tangente = a lo largo del borde) exactamente con la misma formula
que el modo de 2 jugadores usaba en (x, y): la velocidad de salida es
`rapidez * cos(angulo)` a lo largo de la normal y `rapidez * sin(angulo)`
a lo largo de la tangente, con `angulo` proporcional a donde pego en la
pala. Para un borde vertical (normal=(1,0), tangente=(0,1)) esto da
exactamente lo mismo que colisiones.py; ahora solo esta expresado para
cualquier angulo de borde.
"""

import math

import ajustes as cfg


def procesar_borde(bola, borde, pala, eliminado):
    """Devuelve:
      None                                -> no paso nada con este borde
      {"tipo": "rebote", "rapidez": x}    -> reboto (pared fija o pala)
      {"tipo": "perdida"}                 -> cruzo por donde no habia pala: vida perdida
    """
    radio_bola = cfg.BOLA_TAM / 2
    extension = 0.0 if (eliminado or pala is None) else pala.offset_normal
    umbral = radio_bola + extension

    centro_previo = (bola.x_previo + bola.tam / 2, bola.y_previo + bola.tam / 2)
    centro_actual = (bola.x + bola.tam / 2, bola.y + bola.tam / 2)

    d_previo = borde.distancia_normal(centro_previo)
    d_actual = borde.distancia_normal(centro_actual)

    if not (d_previo > umbral >= d_actual):
        return None

    # Interpola el punto exacto del cruce durante este cuadro (mismo
    # principio que el barrido de colisiones._cruce_frontal, pero medido
    # sobre la distancia a la recta del borde en vez de sobre X).
    denominador = d_previo - d_actual
    t = (d_previo - umbral) / denominador if denominador else 0.0
    t = max(0.0, min(1.0, t))
    punto_cruce = (
        centro_previo[0] + (centro_actual[0] - centro_previo[0]) * t,
        centro_previo[1] + (centro_actual[1] - centro_previo[1]) * t,
    )
    s = borde.posicion_tangencial(punto_cruce)

    if not (0 <= s <= borde.longitud):
        return None  # cerca de una esquina: que lo resuelva el borde vecino

    if not eliminado and pala is not None:
        s_min, s_max = pala.rango_s()
        if not (s_min <= s <= s_max):
            return {"tipo": "perdida"}

    rapidez = _rebotar(bola, borde, punto_cruce, s, pala, eliminado, umbral)
    return {"tipo": "rebote", "rapidez": rapidez}


def _rebotar(bola, borde, punto_cruce, s, pala, eliminado, umbral):
    nx, ny = borde.normal
    tx, ty = borde.tangente

    if eliminado or pala is None:
        # Pared fija: reflejo simple, igual que colisiones.chocar_con_paredes
        # (invierte solo la componente perpendicular, conserva la tangencial
        # tal cual). Nadie la controla, asi que no depende de donde pego ni
        # acelera la bola -- las paredes del modo de 2 jugadores tampoco lo
        # hacian.
        v_normal = bola.vx * nx + bola.vy * ny
        v_tangente = bola.vx * tx + bola.vy * ty
        v_normal_saliente = abs(v_normal)  # siempre hacia adentro del campo
        bola.vx = v_normal_saliente * nx + v_tangente * tx
        bola.vy = v_normal_saliente * ny + v_tangente * ty
        rapidez = bola.velocidad
    else:
        # Pala activa: el angulo de salida depende de donde pego, igual que
        # colisiones._rebote_frontal.
        s_min, s_max = pala.rango_s()
        centro_pala = (s_min + s_max) / 2
        mitad = (s_max - s_min) / 2
        desplazamiento = (s - centro_pala) / mitad if mitad else 0.0
        desplazamiento = max(-1.0, min(1.0, desplazamiento))

        rapidez = min(bola.velocidad * cfg.ACELERACION, cfg.BOLA_VEL_MAX)
        angulo = desplazamiento * cfg.BOLA_ANGULO_MAX

        local_normal = rapidez * math.cos(angulo)
        local_tangente = rapidez * math.sin(angulo) + pala.velocidad_actual * cfg.EFECTO_PALA

        bola.vx = local_normal * nx + local_tangente * tx
        bola.vy = local_normal * ny + local_tangente * ty

        # El efecto de la pala puede haber pasado el techo: se vuelve a
        # acotar sin perder la direccion, igual que
        # colisiones._normalizar_velocidad.
        actual = bola.velocidad
        if actual > cfg.BOLA_VEL_MAX:
            factor = cfg.BOLA_VEL_MAX / actual
            bola.vx *= factor
            bola.vy *= factor

    # Deja la bola justo fuera del umbral de choque, nunca atravesandolo.
    bola.x = punto_cruce[0] + nx * umbral - bola.tam / 2
    bola.y = punto_cruce[1] + ny * umbral - bola.tam / 2

    return rapidez
