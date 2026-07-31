# Pong online — triangular, 3 jugadores

Version multijugador de [pong/](../pong/) que corre en el navegador, con un
giro: el campo es un **triangulo** y juegan **3 personas** a la vez, cada una
defendiendo un lado. Servidor autoritativo en Python (FastAPI + WebSocket);
el cliente es HTML/JS/CSS plano sin build ni dependencias — solo dibuja lo
que el servidor manda.

> Este modo **reemplaza** la version anterior de 2 jugadores en campo
> rectangular (queda en el historial de git si hace falta volver a mirarla).

## Como se juega

Cada jugador defiende un lado del triangulo con su pala, que se desliza a lo
largo de ese lado (no arriba/abajo como en el Pong clasico — a lo largo de
tu propio borde, sea cual sea su angulo). Si la pelota se te escapa por una
parte que tu pala no cubre, perdes una vida (arrancas con 3). A la tercera
vida perdida quedas **eliminado**: tu lado se convierte en pared fija — la
pelota sigue rebotando ahi, pero vos ya no podes perder ni ganar nada mas
ahi. Gana el ultimo jugador que le queden vidas.

## Que tiene (todo portado del juego de escritorio, mas lo nuevo del online)

Empujon (dash con Shift) con su impulso (golpe potenciado que acelera la
bola y le cambia el color unos segundos), particulas, estela, brillo,
lineas de escaneo, 6 temas de color, sonido, control por mouse (la pala
sigue al cursor 1 a 1, sin limite de velocidad) y obstaculos que rebotan
solos en el centro del campo.

**Poderes**: pueden convivir varios en el campo a la vez (hasta 4) — cada
tanto aparece uno nuevo sin importar si los anteriores siguen sin agarrar.
Ademas de los 4 de siempre (pala grande, pala chica, bola rapida, bola
lenta), tres nuevos, exclusivos de este modo:

| Poder | Que hace |
| --- | --- |
| `x3` Multibola | Suma bolas extra (clonadas de la que lo toco, con la velocidad rotada un poco para cada lado) hasta un total de 3 en juego. Cualquier bola perdida limpia todas las demas y se vuelve a sacar con una sola. |
| `!!` Empujon sin limite | Durante 6 segundos, tu empujon ignora el tiempo de espera normal — solo te frena la animacion de ida y vuelta (~0.3s), asi que se puede encadenar bastante seguido. |
| `Zz` Paralisis | A un rival al azar le reduce mucho la velocidad de su pala (18% de lo normal) por 4 segundos — y a la vez frena la bola (mismo factor que el poder de bola lenta), para que el paralizado tenga alguna chance real en vez de solo mirar. |

## Que se reutilizo y que se reescribio

`server/entidades.py` (solo `Bola`) y `server/colisiones.py` (para los
obstaculos) siguen siendo **copias identicas** del juego de escritorio —
esa parte de la fisica no dependia de la forma del campo. `server/impulso.py`
tambien quedo identico (solo toca la velocidad de la bola, no le importa la
geometria).

Lo que **si** se reescribio, porque un campo con 3 bordes en angulo es
geometria distinta a un rectangulo:

- `server/geometria.py` (nuevo) — vertices y bordes del triangulo, con la
  normal y tangente de cada lado.
- `server/pala_triangular.py` (nuevo) — la pala vive sobre un borde,
  parametrizada por una posicion a lo largo de el en vez de un Y fijo.
- `server/colisiones_triangulo.py` (nuevo) — el rebote contra un borde
  (pared o pala) calculado en la base local del borde (normal/tangente) en
  vez de en X/Y del campo. Un borde eliminado rebota como pared simple
  (refleja la componente perpendicular, conserva la tangencial — igual que
  las paredes del modo de 2 jugadores); un borde con pala activa rebota con
  angulo segun donde pego, igual que una pala del modo de 2.
- `server/poderes.py` y `server/empujon.py` — misma logica, adaptada a 3
  palas: "quien toco la bola por ultima vez" ahora se rastrea explicito (con
  2 jugadores se podia inferir del signo de la velocidad; con 3 no alcanza),
  y el empujon avanza a lo largo de la normal del borde en vez de "hacia la
  derecha".

**Sobre el mouse sin limite de velocidad**: en teoria, un salto de cursor muy
rapido podria "saltearse" la pelota sin que se detecte el choque. Es un
riesgo aceptado a proposito para un juego casual — en el peor caso se escapa
una vida, nada se rompe. Documentado en `Partida._mover_jugador` en
`server/main.py`.

## Arquitectura

```
pong-online/
  server/
    main.py                FastAPI: cliente + WebSocket /ws + loop de juego
    ajustes.py               constantes de fisica y del triangulo
    geometria.py              vertices/bordes del triangulo (nuevo)
    pala_triangular.py        pala sobre un borde (nuevo)
    colisiones_triangulo.py   rebote bola-borde (nuevo)
    entidades.py               Bola (copia de pong/, Pala ya no se usa)
    colisiones.py               rebote bola-obstaculo (copia de pong/)
    poderes.py                  power-ups, adaptado a 3 palas
    empujon.py                  dash, adaptado a normal de borde
    impulso.py                  golpe potenciado (copia de pong/)
    requirements.txt
  client/
    index.html
    client.js                WebSocket + dibujo en <canvas>, cero fisica ni reglas
    style.css
  PROTOCOLO.md              formato exacto de los mensajes WebSocket
  DEPLOY.md                 como subir esto a un servidor real
```

El servidor es la unica fuente de verdad: calcula toda la fisica y las
reglas a 60 cuadros por segundo, y le manda a los 3 jugadores el estado
completo mas una lista de "eventos" puntuales para que el cliente dispare
particulas y sonido. Los clientes solo mandan input (teclado, mouse, el
disparo del empujon); las particulas, la estela y el sonido son puramente
cosmeticos y viven enteros en el navegador.

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

## Probarlo con 3 jugadores

1. Con el servidor corriendo, abri **tres pestañas** (o tres ventanas) del
   navegador en:

   ```
   http://127.0.0.1:8000
   ```

2. Las primeras dos van a mostrar "Esperando jugadores... (1/3)" y luego
   "(2/3)". Apenas abras la tercera, las tres muestran "Arranco la partida" y
   la pelota empieza a moverse desde el centro.
3. Hace clic dentro de cada pestaña (para que tenga el foco) y proba las
   flechas arriba/abajo en cada una — cada pestaña mueve solo su propia
   pala, sobre su propio lado del triangulo. Tu pala queda marcada con un
   borde blanco.
4. Dejá que la pelota se le escape a un jugador a proposito (no cubras tu
   lado) y confirma que le baja una vida — y que las 3 pestañas lo ven igual.
5. Bajale las 3 vidas al mismo jugador y confirma que su lado se convierte
   en pared (deja de tener pala, pero la pelota sigue rebotando ahi) y que
   el texto dice "eliminado".
6. Seguí jugando hasta que solo quede un jugador con vidas: las 3 pestañas
   tienen que mostrar el panel de fin de partida al mismo tiempo, con
   "GANASTE" en la del ganador y "Jugador N gana" en las otras dos.
7. Proba `Shift` para el empujon (la pala avanza hacia el centro y vuelve),
   el mouse (la pala sigue al cursor de inmediato), y que aparezca algun
   poder y algun obstaculo en el medio del campo.
8. Abri el panel "Ajustes" en una sola pestaña y cambiale el tema — las
   otras dos no se tienen que inmutar, es 100% local de cada navegador.
9. Dejá pasar un rato y confirma que puedan aparecer **varios** poderes a
   la vez (no hace falta agarrar uno para que aparezca el siguiente).
10. Agarra un `x3` (multibola) y confirma que aparezcan bolas extra
    saliendo del mismo punto; despues dejá que se pierda cualquiera de
    ellas y confirma que vuelve a quedar una sola.
11. Agarra un `!!` (empujon sin limite) y probá spamear `Shift` seguido — el
    empujon no deberia frenarse por el cooldown normal mientras dura.
12. Agarra un `Zz` (paralisis) y confirma que a un rival al azar (no a vos)
    se le vea la pala moviendose muy despacio un rato, y que la pelota
    tambien se note mas lenta ese mismo momento.

Si abris una **cuarta** pestaña mientras las otras tres ya estan jugando, esa
queda esperando a que se conecten otras dos para armar el siguiente trio.

### Si algo no anda

- `ModuleNotFoundError: fastapi` → no activaste el entorno virtual o no
  corriste `pip install -r requirements.txt`.
- La pagina carga pero dice "No se pudo conectar al servidor" → revisa que
  uvicorn siga corriendo en la terminal y que la URL sea la que te mostro
  (puerto 8000 por defecto).
- Las pestañas no se sincronizan → asegurate de que las tres apunten al
  mismo servidor (misma URL literal en las tres).
- La pelota rebota rarísimo cerca de una esquina del triangulo → es la parte
  mas delicada de este modo (dos bordes se encuentran ahi); si lo ves,
  contame el momento exacto (que jugador, que esquina) para poder revisarlo.

## Deploy

Ver [DEPLOY.md](DEPLOY.md).
