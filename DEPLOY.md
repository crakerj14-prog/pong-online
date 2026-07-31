# Deploy

## Antes de elegir donde alojarlo, esto importa

Este servidor guarda el estado de las partidas **en memoria del proceso**
(el `Lobby` en `server/lobby.py` y cada `Partida` en `server/partida.py`).
No hay base de datos ni nada compartido entre procesos. Eso tiene dos
consecuencias directas para donde y como lo despliegues:

1. **Tiene que correr como un solo proceso/worker.** Si el hosting levanta
   varias instancias (autoscaling, `--workers 4`, multiples contenedores
   detras de un load balancer sin sticky sessions) dos jugadores que se
   emparejan podrian terminar cada uno hablando con una instancia distinta
   que no sabe nada de la partida del otro. El `Dockerfile` de esta carpeta
   ya fija `--workers 1` a proposito. Si tu plataforma tiene una opcion de
   "instancias" o "replicas", dejala en **1**.
2. **Necesita soporte real de WebSocket con conexiones largas.** Nada de
   "funciones serverless" clasicas (AWS Lambda simple, Vercel Functions,
   Netlify Functions): estas estan pensadas para requests cortos que
   terminan, no para una conexion que queda abierta minutos mientras dura
   una partida. Necesitas un servicio que corra un proceso persistente:
   Render, Fly.io, Railway, un VPS, etc.

Si mas adelante queres escalar a muchas partidas simultaneas en varias
instancias, la solucion es mover el estado de emparejamiento/partida a algo
compartido (Redis, por ejemplo) — pero eso es un cambio de arquitectura, no
un ajuste de configuracion. No hace falta para arrancar.

## El Dockerfile

Ya viene uno en la raiz de `pong-online/` que sirve para cualquiera de las
opciones de abajo que use contenedores. Construye e instala `server/`, copia
`client/` al lado (el servidor sirve esos archivos estaticos desde ahi), y
arranca `uvicorn` escuchando en el puerto que le pase la plataforma via la
variable de entorno `PORT` (con `8000` como default si no la define nadie).

Probalo en local antes de subirlo a cualquier lado:

```
cd pong-online
docker build -t pong-online .
docker run -p 8000:8000 pong-online
```

Y abrí `http://127.0.0.1:8000` en varias pestañas, igual que en el README.

## Opcion recomendada: Render

Es la mas simple para este proyecto: deploy con Docker, soporta WebSocket
sin configuracion extra, y te da una URL `https://` (o sea `wss://` para el
socket) gratis.

1. Subí este repo (o al menos la carpeta `pong-online/`) a GitHub.
2. En [render.com](https://render.com), **New +** → **Web Service**.
3. Conecta el repo. Cuando te pregunte el entorno, elegi **Docker** (Render
   va a detectar el `Dockerfile` solo).
4. Root Directory: `pong-online` (si el `Dockerfile` no esta en la raiz del
   repo sino dentro de esa carpeta).
5. Instance Type: cualquiera sirve para probar; el plan gratuito alcanza
   para vos y hasta tres amigos jugando. **No** subas el "Instance
   Count"/replicas por encima de 1 (ver la seccion de arriba).
6. Deploy. Cuando termine te da una URL tipo
   `https://pong-online-xxxx.onrender.com` — esa es la que abris (o se la
   pasas a tus rivales).

No hace falta que configures el puerto a mano: Render inyecta `PORT` y el
`CMD` del Dockerfile ya lo usa.

## Alternativa: Fly.io

Tambien Docker-based, con una CLI (`flyctl`) en vez de un dashboard web.

```
cd pong-online
flyctl launch          # detecta el Dockerfile, te pregunta nombre y region
flyctl deploy
```

En el `fly.toml` que genera `flyctl launch`, confirma que quede:

```toml
[http_service]
  internal_port = 8000
  force_https = true

[[vm]]
  # no agregues 'count' o 'processes' con mas de 1 instancia
```

## Alternativa: VPS propio (mas manual, mas control)

Si tenes una maquina Linux (DigitalOcean, un VPS barato, lo que sea) y
preferis no depender de una plataforma:

1. Instala Python 3.9+ y Git en el servidor.
2. Cloná el repo y segui los pasos de "Correr en local" del README, pero
   sin `--reload` (eso es solo para desarrollo):
   ```
   cd pong-online/server
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Corré uvicorn como servicio permanente con `systemd`. Crea
   `/etc/systemd/system/pong-online.service`:
   ```ini
   [Unit]
   Description=Pong online
   After=network.target

   [Service]
   User=tu_usuario
   WorkingDirectory=/ruta/a/pong-online/server
   ExecStart=/ruta/a/pong-online/server/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   Despues: `sudo systemctl enable --now pong-online`.
4. Para exponerlo en `https://` (necesario para que `wss://` funcione desde
   un dominio propio) lo mas simple es poner **Caddy** adelante, que saca el
   certificado TLS solo:
   ```
   sudo apt install caddy
   ```
   `/etc/caddy/Caddyfile`:
   ```
   tu-dominio.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```
   `sudo systemctl reload caddy`. Con eso el WebSocket queda accesible en
   `wss://tu-dominio.com/ws` sin tocar nada del codigo (el cliente ya arma
   la URL solo, mirando si la pagina es `https:` para usar `wss:`).

## Despues de desplegar

- Probá desde varios dispositivos en redes distintas (no todos en tu wifi
  de casa) para confirmar que no hay ningun firewall/proxy bloqueando
  WebSocket en el medio.
- Si alguien queda pegado esperando en el lobby y nunca avanza, revisa los
  logs de la plataforma — casi siempre es la conexion WebSocket que no esta
  llegando (falta `wss://`, o el proxy delante no la deja pasar).
- Recorda: reiniciar el servicio (redeploy, restart manual, o que se caiga
  y vuelva a levantar solo) borra cualquier partida en curso, porque todo
  vive en memoria. Nadie pierde datos importantes, pero si estan jugando en
  ese momento se les corta.
