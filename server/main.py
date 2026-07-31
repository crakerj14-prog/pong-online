"""Punto de entrada FastAPI: sirve los archivos estaticos del cliente y
expone el WebSocket /ws. Toda la logica vive en modulos aparte, cada uno
con una sola responsabilidad:

  jugador.py    -- que es un jugador conectado (el WebSocket y su input).
  obstaculos.py -- los bloques que rebotan solos en el centro del campo.
  partida.py    -- la fisica y el estado de una partida en curso.
  lobby.py      -- emparejamiento: junta gente hasta armar un grupo del
                    tamano que elige el anfitrion, y el ciclo de vida de
                    cada conexion mientras juega.

Ver PROTOCOLO.md para el formato exacto de los mensajes WebSocket, y
README.md para como corre todo esto junto (2, 3 o 4 jugadores; rectangulo,
triangulo o cuadrado segun la cantidad).

Ejecutar con:  uvicorn main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from lobby import manejar_conexion

RAIZ = Path(__file__).resolve().parent
CLIENTE_DIR = RAIZ.parent / "client"

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manejar_conexion(ws)


# Se monta al final: la ruta declarada arriba (/ws) tiene prioridad sobre
# este catch-all de archivos estaticos.
app.mount("/", StaticFiles(directory=CLIENTE_DIR, html=True), name="cliente")
