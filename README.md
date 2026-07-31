# Pong online — 2 a 4 jugadores

Pong multijugador en tiempo real que corre en el navegador. Antes de
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

## Que tiene

Empujon (dash con Shift) con su impulso (golpe potenciado que acelera la
bola y le cambia el color unos segundos), particulas, estela, brillo,
lineas de escaneo, 6 temas de color, sonido, musica de fondo (un loop corto
generado con Web Audio, sin ningun archivo de audio de por medio — igual que
los efectos), control por mouse (la pala sigue al cursor 1 a 1, sin limite
de velocidad) y obstaculos que rebotan solos en el centro del campo. **Todo
funciona igual en los 3 modos** (2, 3 o 4 jugadores) — no hay nada exclusivo
de un tamaño de partida.

La musica y los efectos de sonido se controlan por separado desde
"Ajustes" ("Musica" / "Sonido"): la musica arranca bastante mas baja de
volumen que los efectos a proposito, para no taparlos ni cansar en
partidas largas.

**Poderes**: pueden convivir varios en el campo a la vez (hasta 4) — cada
tanto aparece uno nuevo sin importar si los anteriores siguen sin agarrar.
Ademas de los 4 de siempre (pala grande, pala chica, bola rapida, bola
lenta), tres mas:

| Poder | Que hace |
| --- | --- |
| `x3` Multibola | Suma bolas extra (clonadas de la que lo toco, con la velocidad rotada un poco para cada lado) hasta un total de 3 en juego. Cualquier bola perdida limpia todas las demas y se vuelve a sacar con una sola. |
| `!!` Empujon sin limite | Durante 6 segundos, tu empujon ignora el tiempo de espera normal — solo te frena la animacion de ida y vuelta (~0.3s), asi que se puede encadenar bastante seguido. |
| `Zz` Paralisis | A un rival al azar le reduce mucho la velocidad de su pala (18% de lo normal) por 4 segundos — y a la vez frena la bola (mismo factor que el poder de bola lenta), para que el paralizado tenga alguna chance real en vez de solo mirar. |

## Como esta organizada la fisica

`server/entidades.py` (la `Bola`), `server/colisiones.py` (rebote contra los
obstaculos) y `server/impulso.py` (el golpe potenciado) son las piezas que
no dependen para nada de la forma del campo — mueven una bola en X/Y contra
una caja fija o le tocan la velocidad, nada mas.

Lo que sabe de geometria, para que un mismo campo pueda ser rectangulo,
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
- `server/partida.py` — la `Partida` distingue "indice de borde" (puede
  haber mas lados que jugadores, como en el rectangulo) de "indice de
  jugador" — todo lo demas (vidas, poderes, empujones) esta indexado por
  jugador, no por borde.
- `server/lobby.py` — el `Lobby` (eleccion del anfitrion, matchmaking) no
  sabe nada de fisica: arma el grupo y le entrega la lista de jugadores a
  `Partida`, que es quien decide que forma darle al campo.

**Sobre el mouse sin limite de velocidad**: en teoria, un salto de cursor muy
rapido podria "saltearse" la pelota sin que se detecte el choque. Es un
riesgo aceptado a proposito para un juego casual — en el peor caso se escapa
una vida, nada se rompe. Documentado en `Partida._mover_jugador` en
`server/partida.py`.

## Arquitectura

```
pong-online/
  server/
    main.py                   FastAPI: monta el cliente estatico + /ws (el unico punto de entrada)
    lobby.py                    emparejamiento (Lobby) y ciclo de vida de cada conexion
    partida.py                  fisica y estado de una partida en curso (Partida)
    jugador.py                  que es un jugador conectado (WebSocket + input)
    obstaculos.py                bloques que rebotan solos en el centro del campo
    ajustes.py                 constantes de fisica (rectangulo/triangulo/cuadrado)
    geometria.py                vertices/bordes segun cantidad de jugadores
    pala_triangular.py          pala sobre un borde
    colisiones_triangulo.py     rebote bola-borde (pared o pala)
    entidades.py                 la Bola (geometria-agnostica)
    colisiones.py                 rebote bola-obstaculo
    poderes.py                   power-ups, indexado por jugador (0-based)
    empujon.py                   dash, adaptado a normal de borde
    impulso.py                   golpe potenciado
    requirements.txt
  client/
    index.html                 incluye la UI de eleccion de cantidad (lobby)
    style.css
    js/
      main.js                   punto de entrada: conecta y cablea el resto de los modulos
      red.js                    WebSocket: conectar/mandar, reparte mensajes por "type"
      lobby.js                   botones de eleccion de cantidad (solo los ve el anfitrion)
      juego.js                   traduce inicio/estado/rival_desconectado a estado.js + efectos
      estado.js                   estado compartido (geometria, los 2 ultimos "estado", tu numero)
      interpolacion.js             suaviza las posiciones entre paquete y paquete
      dibujo.js                   todo el <canvas>: pinta lo que hay en estado.js, cero fisica
      lienzo.js                    el <canvas>/contexto + primitivas de dibujo (rect, brillo)
      efectos.js                   particulas y estela de la bola
      audio.js                     efectos de sonido (Web Audio, sin archivos)
      musica.js                    loop de musica de fondo (Web Audio, sin archivos)
      entrada.js                   teclado, mouse, y el primer gesto que desbloquea el audio
      ajustes.js                   ajustes persistidos en localStorage + panel de UI
      temas.js                     paletas de color
  PROTOCOLO.md                 formato exacto de los mensajes WebSocket
  DEPLOY.md                    como subir esto a un servidor real
```

El servidor es la unica fuente de verdad: calcula toda la fisica y las
reglas a 60 cuadros por segundo, y le manda a todos los jugadores el estado
completo mas una lista de "eventos" puntuales para que el cliente dispare
particulas y sonido. Los clientes solo mandan input (teclado, mouse, el
disparo del empujon, la eleccion de cantidad de jugadores si sos el
anfitrion); las particulas, la estela, la musica y el sonido son puramente
cosmeticos y viven enteros en el navegador.

Tanto el cliente como el servidor estan organizados por responsabilidad, no
por tamaño: cada modulo hace una sola cosa (red, dibujo, audio, matchmaking,
fisica...) y se importa donde hace falta. El cliente usa modulos ES nativos
del navegador (`<script type="module">`) — nada de bundler ni paso de build,
sigue siendo HTML/JS/CSS plano.

### Sobre la fluidez del movimiento

Dos detalles que no son obvios pero hacen toda la diferencia en como se
siente el juego:

- **El servidor duerme hasta un vencimiento fijo**, no un rato fijo despues
  de trabajar (ver `bucle_partida` en `server/partida.py`). Dormir `1/FPS`
  al final de cada vuelta daria un periodo real de `trabajo + 1/FPS`, o sea
  menos cuadros por segundo de los que dice, y variable segun la carga de la
  maquina. Como la bola avanza una vez por cuadro, un servidor lento no se
  "ve entrecortado": **juega en camara lenta**. Pesa especialmente en
  hosting con CPU compartida.
- **El cliente interpola entre los dos ultimos estados** recibidos (ver
  `client/js/interpolacion.js`), en vez de dibujar siempre el ultimo. El
  navegador dibuja a la tasa de tu monitor y los paquetes llegan con jitter:
  sin interpolar, cada paquete demorado se ve como un micro-tiron. El costo
  es dibujar ~17ms en el pasado, despreciable al lado del viaje de ida y
  vuelta al servidor que ya existe.

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
12. Hace clic en algun lado de la pagina (el navegador necesita ese primer
    gesto para permitir audio) y confirma que arranca la musica de fondo,
    notablemente mas baja que los pitidos de los golpes. Apagala y prendela
    de nuevo desde "Ajustes" → "Musica" y confirma que corta y vuelve a
    arrancar sin quedar sonidos pisados ni superpuestos.

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
