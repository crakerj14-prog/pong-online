# Pong online — 2 a 4 jugadores

Version multijugador de [pong/](../pong/) que corre en el navegador. Antes de
arrancar, el anfitrion (el primero en conectarse) elige cuantos van a jugar:
**2, 3 o 4**. La forma del campo cambia segun esa eleccion — rectangulo
clasico para 2, triangulo para 3, cuadrado para 4 — y cada jugador defiende
un lado. Servidor autoritativo en Python (FastAPI + WebSocket); el cliente
es HTML/JS/CSS plano sin build ni dependencias — solo dibuja lo que el
servidor manda.

## Como se juega

1. Al conectarte, si sos el primero (el "anfitrion") elegis cuantos van a
   jugar (2, 3 o 4) apenas haya suficiente gente conectada para esa opcion —
   podes esperar tranquilo aunque ya haya 2 conectados, no hace falta
   arrancar apenas se pueda. Los demas ven ese mismo estado en modo
   solo-lectura ("esperando a que el anfitrion elija").
2. En cuanto se junta la cantidad elegida, arranca la partida para ese
   grupo. Si sobra gente en el lobby, se queda esperando al siguiente grupo
   (el primero que quede pasa a ser el nuevo anfitrion).
3. Cada jugador defiende un lado de la forma con su pala, que se desliza a
   lo largo de ese lado (no arriba/abajo como en el Pong clasico — a lo
   largo de tu propio borde, sea cual sea su angulo). Si la pelota se te
   escapa por una parte que tu pala no cubre, perdes una vida (arrancas con
   3). A la tercera vida perdida quedas **eliminado**: tu lado se convierte
   en pared fija — la pelota sigue rebotando ahi, pero vos ya no podes
   perder ni ganar nada mas ahi. Gana el ultimo jugador al que le queden
   vidas.
4. Con 2 jugadores el campo es un rectangulo de 4 lados, pero solo
   izquierda/derecha son de jugador — arriba/abajo son paredes fijas desde
   el arranque, igual que en el Pong clasico de toda la vida.

## Que tiene (todo portado del juego de escritorio, mas lo nuevo del online)

Empujon (dash con Shift) con su impulso (golpe potenciado que acelera la
bola y le cambia el color unos segundos), particulas, estela, brillo,
lineas de escaneo, 6 temas de color, sonido, control por mouse (la pala
sigue al cursor 1 a 1, sin limite de velocidad) y obstaculos que rebotan
solos en el centro del campo. **Todo funciona igual en los 3 modos** (2, 3 o
4 jugadores) — no hay nada exclusivo de un tamaño de partida.

**Poderes**: pueden convivir varios en el campo a la vez (hasta 4) — cada
tanto aparece uno nuevo sin importar si los anteriores siguen sin agarrar.
Ademas de los 4 de siempre (pala grande, pala chica, bola rapida, bola
lenta), tres mas:

| Poder | Que hace |
| --- | --- |
| `x3` Multibola | Suma bolas extra (clonadas de la que lo toco, con la velocidad rotada un poco para cada lado) hasta un total de 3 en juego. Cualquier bola perdida limpia todas las demas y se vuelve a sacar con una sola. |
| `!!` Empujon sin limite | Durante 6 segundos, tu empujon ignora el tiempo de espera normal — solo te frena la animacion de ida y vuelta (~0.3s), asi que se puede encadenar bastante seguido. |
| `Zz` Paralisis | A un rival al azar le reduce mucho la velocidad de su pala (18% de lo normal) por 4 segundos — y a la vez frena la bola (mismo factor que el poder de bola lenta), para que el paralizado tenga alguna chance real en vez de solo mirar. |

## Que se reutilizo y que se reescribio

`server/entidades.py` (solo `Bola`) y `server/colisiones.py` (para los
obstaculos) siguen siendo **copias identicas** del juego de escritorio —
esa parte de la fisica no depende de la forma del campo. `server/impulso.py`
tambien quedo identico (solo toca la velocidad de la bola, no le importa la
geometria).

Lo que **si** se reescribio, para que un mismo campo pueda ser rectangulo,
triangulo o cuadrado sin duplicar la fisica:

- `server/geometria.py` — `construir(cantidad_jugadores)` arma vertices y
  bordes segun la cantidad (2 → rectangulo con 2 de 4 lados sin dueño desde
  el arranque; 3/4 → poligono regular donde todos los lados son de
  jugador), y devuelve el mapeo jugador→borde.
- `server/pala_triangular.py` — la pala vive sobre un borde, parametrizada
  por una posicion a lo largo de el en vez de un Y fijo (le da lo mismo que
  forma tenga el campo).
- `server/colisiones_triangulo.py` — el rebote contra un borde (pared o
  pala) calculado en la base local del borde (normal/tangente) en vez de en
  X/Y del campo. Un borde sin pala (eliminado, o pared fija desde el
  arranque como arriba/abajo del rectangulo de 2) rebota como pared simple
  (refleja la componente perpendicular, conserva la tangencial); un borde
  con pala activa rebota con angulo segun donde pego. Esta unica pieza de
  codigo cubre los 3 modos sin ninguna rama especial por cantidad de
  jugadores.
- `server/poderes.py` y `server/empujon.py` — indexados por jugador
  (0-based), no por cantidad fija: "quien toco la bola por ultima vez" se
  rastrea explicito (con 2 jugadores en el Pong clasico se podia inferir
  del signo de la velocidad; con 3 o 4 no alcanza), y el empujon avanza a lo
  largo de la normal del borde en vez de "hacia la derecha".
- `server/main.py` — el `Lobby` (eleccion del anfitrion, matchmaking) y la
  `Partida` distinguen "indice de borde" (puede haber mas lados que
  jugadores, como en el rectangulo) de "indice de jugador" — todo lo demas
  (vidas, poderes, empujones) esta indexado por jugador, no por borde.

**Sobre el mouse sin limite de velocidad**: en teoria, un salto de cursor muy
rapido podria "saltearse" la pelota sin que se detecte el choque. Es un
riesgo aceptado a proposito para un juego casual — en el peor caso se escapa
una vida, nada se rompe. Documentado en `Partida._mover_jugador` en
`server/main.py`.

## Arquitectura

```
pong-online/
  server/
    main.py                FastAPI: cliente + WebSocket /ws + Lobby + loop de juego
    ajustes.py               constantes de fisica (rectangulo/triangulo/cuadrado)
    geometria.py              vertices/bordes segun cantidad de jugadores
    pala_triangular.py        pala sobre un borde
    colisiones_triangulo.py   rebote bola-borde (pared o pala)
    entidades.py               Bola (copia de pong/, Pala ya no se usa)
    colisiones.py               rebote bola-obstaculo (copia de pong/)
    poderes.py                  power-ups, indexado por jugador (0-based)
    empujon.py                  dash, adaptado a normal de borde
    impulso.py                  golpe potenciado (copia de pong/)
    requirements.txt
  client/
    index.html                incluye la UI de eleccion de cantidad (lobby)
    client.js                WebSocket + dibujo en <canvas>, cero fisica ni reglas
    style.css
  PROTOCOLO.md              formato exacto de los mensajes WebSocket
  DEPLOY.md                 como subir esto a un servidor real
```

El servidor es la unica fuente de verdad: calcula toda la fisica y las
reglas a 60 cuadros por segundo, y le manda a todos los jugadores el estado
completo mas una lista de "eventos" puntuales para que el cliente dispare
particulas y sonido. Los clientes solo mandan input (teclado, mouse, el
disparo del empujon, la eleccion de cantidad de jugadores si sos el
anfitrion); las particulas, la estela y el sonido son puramente cosmeticos y
viven enteros en el navegador.

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

## Probarlo

1. Con el servidor corriendo, abri **al menos tres pestañas** (o ventanas)
   del navegador en:

   ```
   http://127.0.0.1:8000
   ```

2. La primera pestaña es la anfitriona: le van a aparecer botones **2 / 3 /
   4** (deshabilitados los que todavia no tienen suficiente gente
   conectada). Las demas ven un texto de espera, sin botones.
3. Con dos pestañas abiertas, elegi **2** en la anfitriona: arranca de
   inmediato un campo rectangular clasico. Recarga ambas y probá con **3**
   pestañas abiertas eligiendo **3** (triangulo) y con **4** eligiendo
   **4** (cuadrado).
4. Hace clic dentro de cada pestaña (para que tenga el foco) y proba las
   flechas arriba/abajo en cada una — cada pestaña mueve solo su propia
   pala, sobre su propio lado. Tu pala queda marcada con un borde blanco.
5. Dejá que la pelota se le escape a un jugador a proposito (no cubras tu
   lado) y confirma que le baja una vida — y que todas las pestañas lo ven
   igual.
6. Bajale todas las vidas al mismo jugador y confirma que su lado se
   convierte en pared (deja de tener pala, pero la pelota sigue rebotando
   ahi) y que el texto dice "eliminado".
7. Seguí jugando hasta que solo quede un jugador con vidas: todas las
   pestañas tienen que mostrar el panel de fin de partida al mismo tiempo,
   con "GANASTE" en la del ganador y "Jugador N gana" en las demas.
8. Proba `Shift` para el empujon (la pala avanza hacia el centro y vuelve),
   el mouse (la pala sigue al cursor de inmediato), y que aparezca algun
   poder y algun obstaculo en el medio del campo — en los 3 modos.
9. Abri el panel "Ajustes" en una sola pestaña y cambiale el tema — las
   otras no se tienen que inmutar, es 100% local de cada navegador.
10. Con una quinta pestaña abierta mientras un grupo ya esta jugando: tiene
    que quedar esperando en un lobby nuevo (no se mete en la partida en
    curso), y si esa quinta se desconecta antes de que se junte su grupo,
    las que queden tienen que seguir viendo el lobby bien.
11. Desconecta al anfitrion **antes** de que elija cantidad (cerrale la
    pestaña) y confirma que el siguiente en la fila pasa a ser anfitrion y
    le aparecen los botones (sin heredar ninguna eleccion vieja).

### Si algo no anda

- `ModuleNotFoundError: fastapi` → no activaste el entorno virtual o no
  corriste `pip install -r requirements.txt`.
- La pagina carga pero dice "No se pudo conectar al servidor" → revisa que
  uvicorn siga corriendo en la terminal y que la URL sea la que te mostro
  (puerto 8000 por defecto).
- Las pestañas no se sincronizan → asegurate de que todas apunten al mismo
  servidor (misma URL literal).
- La pelota rebota rarísimo cerca de una esquina del campo → es la parte
  mas delicada de este modo (dos bordes se encuentran ahi); si lo ves,
  contame el momento exacto (que jugador, que esquina, que cantidad de
  jugadores) para poder revisarlo.

## Deploy

Ver [DEPLOY.md](DEPLOY.md).
