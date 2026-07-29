# Pong online

Version multijugador de [pong/](../pong/) que corre en el navegador. Servidor
autoritativo en Python (FastAPI + WebSocket); el cliente es HTML/JS/CSS plano
sin build ni dependencias — solo dibuja lo que el servidor manda.

## Que se reutilizo del juego de escritorio

`server/entidades.py`, `server/colisiones.py`, `server/poderes.py`,
`server/empujon.py` y `server/impulso.py` son **copias identicas** de sus
equivalentes en `pong/`: toda esa fisica y esas reglas ya estaban libres de
tkinter (no dibujaban ni tocaban sonido), asi que corren en el servidor sin
cambiarles una linea. `server/ajustes.py` es nuevo, con los mismos nombres de
constante que `pong/ajustes.py` para que esos archivos copiados funcionen tal
cual.

Es el mismo juego que tenes en local: palas, pelota, marcador, **poderes**
(pala grande / pala chica / bola rapida / bola lenta), **empujon** (dash con
Shift) con su **impulso** (golpe potenciado que acelera la bola y le cambia
el color unos segundos), particulas, estela, brillo, lineas de escaneo, los
6 temas de color, y sonido. Ademas, exclusivo de esta version online: control
por **mouse** (la pala sigue al cursor 1 a 1, sin limite de velocidad — mover
las flechas te devuelve al control por teclado) y **obstaculos** que rebotan
solos en el medio del campo.

Los obstaculos se implementaron reusando `colisiones.resolver_pala` tal cual:
para la fisica, un obstaculo es una pala mas, solo que nadie la controla y se
mueve sola. Estan confinados a la franja central (`OBSTACULO_ZONA_X` en
`server/ajustes.py`) para no invadir nunca la zona de las palas.

**Sobre el mouse sin limite de velocidad**: en teoria, un salto de cursor muy
rapido podria "saltearse" la pelota sin que se detecte el choque (la
deteccion de colisiones esta pensada para el movimiento de la pelota, no para
que la pala misma salte de golpe). Es un riesgo aceptado a proposito para un
juego casual — en el peor caso se escapa un punto, nada se rompe. Esta
documentado en `Partida._mover_jugador` en `server/main.py` por si algun dia
hace falta ponerle un limite.

Lo unico que no tiene sentido en un lobby de dos jugadores remotos —
seleccionar dificultad de CPU, elegir puntos para ganar antes de empezar — se
dejo fijo en `server/ajustes.py` (7 puntos, la misma aceleracion que el nivel
"Normal" del escritorio). Tema, brillo, estela, particulas, scanlines y
sonido son 100% cosmeticos y cada jugador los elige en su propio navegador
(se guardan en `localStorage`, el equivalente web del `ajustes.json` de
escritorio) — el servidor ni se entera de que tema tiene puesto cada uno.

## Arquitectura

```
pong-online/
  server/
    main.py         FastAPI: sirve el cliente + WebSocket /ws + loop de juego
    ajustes.py       constantes de fisica (ver nota arriba)
    entidades.py      Pala, Bola (copia de pong/)
    colisiones.py      rebotes pared/pala (copia de pong/)
    poderes.py         power-ups (copia de pong/)
    empujon.py         dash de la pala (copia de pong/)
    impulso.py         golpe potenciado que deja un dash (copia de pong/)
    requirements.txt
  client/
    index.html
    client.js         WebSocket + dibujo en <canvas>, cero fisica ni reglas
    style.css
  PROTOCOLO.md       formato exacto de los mensajes WebSocket
  DEPLOY.md          como subir esto a un servidor real
```

El servidor es la unica fuente de verdad: calcula toda la fisica y las reglas
a 60 cuadros por segundo, y le manda a los dos jugadores el estado completo
mas una lista de "eventos" puntuales (golpes, puntos, poderes recogidos) para
que el cliente dispare particulas y sonido. Los clientes solo mandan que
teclas tienen apretadas y cuando se dispara el empujon; las particulas, la
estela y el sonido son puramente cosmeticos y viven enteros en el navegador,
reaccionando a esos eventos — el servidor no sabe ni le importa si hay una
chispita en pantalla.

## Correr en local

Necesitas Python 3.9 o mas nuevo.

```
cd pong-online/server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

(en Linux/Mac el activate es `source venv/bin/activate`)

Vas a ver algo como `Uvicorn running on http://127.0.0.1:8000`.

## Probarlo con dos jugadores

1. Con el servidor corriendo, abri **dos pestañas** (o dos ventanas) del
   navegador en:

   ```
   http://127.0.0.1:8000
   ```

2. En la primera pestaña vas a ver "Esperando a un oponente...". Apenas
   abras la segunda pestaña, las dos van a mostrar "Arranco la partida" y
   la pelota va a empezar a moverse.
3. Hace clic dentro de cada pestaña (para que tenga el foco) y proba las
   flechas arriba/abajo — cada pestaña mueve solo su propia pala. La pala
   que controlas queda marcada con un borde blanco.
4. Confirma que en las dos pestañas la pelota se ve en la misma posicion al
   mismo tiempo, y que el marcador sube en ambas cuando alguien anota.
5. Proba `Shift` para el empujon: la pala tiene que salir disparada hacia el
   centro y volver sola, y la barrita de cooldown (esquina inferior) tiene
   que vaciarse y volver a llenarse en unos 9 segundos. Si conecta con la
   bola mientras va de ida, la bola cambia de color un rato.
6. Dejá pasar unos segundos y confirma que aparezca el icono de un poder en
   el centro del campo, y que agarrarlo con la bola cambie algo (una pala
   crece/encoge, o la bola pega un salto de velocidad).
7. Abri el panel "Ajustes" (abajo del campo) en una sola pestaña y cambiale
   el tema o apagale las particulas — la otra pestaña no se tiene que
   inmutar, porque es una preferencia 100% local de cada navegador.
8. Movete con el mouse sobre el campo: la pala tiene que seguir al cursor de
   inmediato (no a la velocidad fija del teclado). Apretá una flecha y
   confirma que vuelve a mandar el teclado.
9. Confirma que los dos bloques que rebotan en el medio del campo se muevan
   solos y que la bola rebote contra ellos igual que contra una pala.

Si abris una **tercera** pestaña mientras las otras dos estan jugando, esa
queda esperando a que se libere un lugar (arranca su propia partida en
cuanto se conecte una cuarta).

### Si algo no anda

- `ModuleNotFoundError: fastapi` → no activaste el entorno virtual o no
  corriste `pip install -r requirements.txt`.
- La pagina carga pero dice "No se pudo conectar al servidor" → revisa que
  uvicorn siga corriendo en la terminal y que la URL sea la que te mostro
  (puerto 8000 por defecto).
- Las pestañas no se sincronizan / cada una mueve las dos palas → asegurate
  de que las dos pestañas apunten al mismo servidor (no una a `127.0.0.1` y
  otra a `localhost`, aunque en teoria son lo mismo — si algo raro pasa,
  usa la misma URL literal en ambas).

## Deploy

Ver [DEPLOY.md](DEPLOY.md).
