"""Emparejamiento: junta gente en un lobby hasta que el anfitrion (el
primero en conectarse) elige cuantos van a jugar y hay suficientes
conectados para esa cantidad, y despues maneja la conexion mientras la
partida esta en curso.

Solo hay un `Lobby` global a la vez: en cuanto arranca una partida, si sobra
gente esperando, se queda un `Lobby` nuevo para el siguiente grupo.
"""

from __future__ import annotations

import asyncio

from fastapi import WebSocket, WebSocketDisconnect

import ajustes as cfg
from jugador import Jugador
from partida import Partida, bucle_partida


class Lobby:
    """Gente esperando armar partida. El primero en conectarse es el
    anfitrion: el unico que puede elegir cuantos van a jugar (2 a 4). En
    cuanto hay suficientes conectados para la cantidad elegida, arranca."""

    def __init__(self, primer_jugador):
        self.jugadores = [primer_jugador]
        self.cantidad_elegida = None

    @property
    def anfitrion(self):
        return self.jugadores[0] if self.jugadores else None

    def agregar(self, jugador):
        self.jugadores.append(jugador)

    def quitar(self, jugador):
        """Si `jugador` era el anfitrion, el siguiente en la fila pasa a
        serlo y se resetea la eleccion (para que decida de nuevo: no
        heredar una cantidad que nunca eligio)."""
        era_anfitrion = self.jugadores and jugador is self.jugadores[0]
        self.jugadores.remove(jugador)
        if era_anfitrion:
            self.cantidad_elegida = None

    @property
    def lista_para_arrancar(self):
        return self.cantidad_elegida is not None and len(self.jugadores) >= self.cantidad_elegida

    def tomar_jugadores(self):
        """Saca del lobby a los primeros `cantidad_elegida` (los que
        arrancan la partida); los que sobran quedan para el siguiente."""
        n = self.cantidad_elegida
        elegidos, self.jugadores = self.jugadores[:n], self.jugadores[n:]
        self.cantidad_elegida = None
        return elegidos


async def _avisar_estado(lobby_actual: Lobby):
    conectados = len(lobby_actual.jugadores)
    for indice, jugador in enumerate(lobby_actual.jugadores):
        if indice == 0:
            mensaje = {
                "type": "elegir",
                "conectados": conectados,
                "opciones": list(cfg.CANTIDADES_JUGADORES_POSIBLES),
                "cantidad_elegida": lobby_actual.cantidad_elegida,
            }
        else:
            mensaje = {
                "type": "esperando",
                "conectados": conectados,
                "cantidad_elegida": lobby_actual.cantidad_elegida,
            }
        try:
            await jugador.ws.send_json(mensaje)
        except Exception:
            pass  # se entera por su propio receive_json() si se desconecto


async def _arrancar_partida(grupo):
    for indice, j in enumerate(grupo):
        j.numero = indice + 1
    partida = Partida(grupo)
    for j in grupo:
        j.partida = partida

    base_inicio = {
        "campo": {"ancho": cfg.ANCHO, "alto": cfg.ALTO},
        "vertices": [list(v) for v in partida.vertices],
        "bordes": [
            {"a": list(b.a), "b": list(b.b), "angulo": b.angulo}
            for b in partida.bordes
        ],
        # jugador_bordes[i] = indice de borde del jugador i (0-based): con 2
        # jugadores no coincide con el indice del jugador (el rectangulo
        # tiene 4 bordes, solo 2 son de jugador).
        "jugador_bordes": [partida.mapeo_jugador_a_borde[i] for i in range(len(grupo))],
        "pala": {"largo": cfg.PALA_LARGO, "grosor": cfg.PALA_GROSOR},
        "bola": {"tam": cfg.BOLA_TAM},
        "poder_tam": cfg.PODER_TAM,
        "vidas_iniciales": cfg.VIDAS_INICIALES,
        "cantidad_jugadores": len(grupo),
    }
    for j in grupo:
        await j.ws.send_json({"type": "inicio", "numero": j.numero, **base_inicio})

    asyncio.create_task(bucle_partida(partida))


_lobby: Lobby | None = None
_lock = asyncio.Lock()


async def manejar_conexion(ws: WebSocket):
    """Todo el ciclo de vida de una conexion: acepta, la mete en el lobby
    (o arranca partida de una si con ella se completa un grupo), procesa
    sus mensajes mientras juega, y limpia el lobby o avisa a sus companeros
    de partida cuando se desconecta."""
    global _lobby
    await ws.accept()
    jugador = Jugador(ws)

    async with _lock:
        if _lobby is None:
            _lobby = Lobby(jugador)
        else:
            _lobby.agregar(jugador)
        await _avisar_estado(_lobby)

        if _lobby.lista_para_arrancar:
            grupo = _lobby.tomar_jugadores()
            if not _lobby.jugadores:
                _lobby = None
            await _arrancar_partida(grupo)

    try:
        while True:
            mensaje = await ws.receive_json()
            tipo = mensaje.get("type")

            if tipo == "elegir_cantidad":
                async with _lock:
                    if _lobby is not None and jugador is _lobby.anfitrion:
                        cantidad = mensaje.get("cantidad")
                        if cantidad in cfg.CANTIDADES_JUGADORES_POSIBLES:
                            _lobby.cantidad_elegida = cantidad
                            await _avisar_estado(_lobby)
                            if _lobby.lista_para_arrancar:
                                grupo = _lobby.tomar_jugadores()
                                if not _lobby.jugadores:
                                    _lobby = None
                                await _arrancar_partida(grupo)
            elif tipo == "input":
                tecla = mensaje.get("tecla")
                presionada = bool(mensaje.get("presionada"))
                if tecla == "arriba":
                    jugador.arriba = presionada
                elif tecla == "abajo":
                    jugador.abajo = presionada
                jugador.modo_control = "teclado"
            elif tipo == "mouse":
                x, y = mensaje.get("x"), mensaje.get("y")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    jugador.mouse_x = float(x)
                    jugador.mouse_y = float(y)
                    jugador.modo_control = "mouse"
            elif tipo == "accion":
                if mensaje.get("accion") == "empujon" and jugador.partida is not None:
                    jugador.partida.activar_empujon(jugador.numero - 1)
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            if _lobby is not None and jugador in _lobby.jugadores:
                _lobby.quitar(jugador)
                if not _lobby.jugadores:
                    _lobby = None
                else:
                    await _avisar_estado(_lobby)

        if jugador.partida is not None:
            jugador.partida.activa = False
            for otro in jugador.partida.jugadores:
                if otro is not jugador:
                    try:
                        await otro.ws.send_json({"type": "rival_desconectado"})
                    except Exception:
                        pass
