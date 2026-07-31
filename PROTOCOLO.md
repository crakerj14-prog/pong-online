# Protocolo WebSocket

Todos los mensajes son JSON con un campo `"type"`. Conexion en `/ws`.

Partidas de 2, 3 o 4 jugadores, cada uno defiende un lado del campo. La
cantidad la elige el anfitrion (el primero en conectarse a cada lobby) una
vez que hay al menos esa cantidad de gente esperando; ver la seccion de
lobby mas abajo. El campo es siempre un cuadrado de `campo.ancho` x
`campo.alto`, con la forma real (rectangulo/triangulo/cuadrado) inscripta
adentro; el servidor manda las coordenadas de los vertices y bordes una
sola vez (en `inicio`) porque no cambian durante la partida.

Con 2 jugadores el campo tiene 4 bordes pero solo 2 son de jugador
(izquierda/derecha); arriba/abajo son paredes fijas desde el arranque —
`jugador_bordes` (ver `inicio`) es lo que le dice al cliente que borde
mirar para cada jugador, porque con 2 el indice de jugador ya no coincide
con el indice de borde.

## Lobby (antes de `inicio`)

### `elegir`
Se manda solo al anfitrion (primero en conectarse al lobby actual), cada
vez que cambia la cantidad de gente esperando o el elige una cantidad.
```json
{ "type": "elegir", "conectados": 2, "opciones": [2, 3, 4], "cantidad_elegida": null }
```
El cliente le muestra botones 2/3/4 (deshabilitados si `conectados` es menor
a esa opcion) para que elija. Si ya eligio antes y siguen faltando jugadores,
`cantidad_elegida` viene con ese valor (para que el cliente marque la opcion
ya elegida en vez de mostrar todo sin marcar).

### `esperando`
Se manda a todos menos al anfitrion, con la misma informacion en modo
solo-lectura (no hay botones que mostrar).
```json
{ "type": "esperando", "conectados": 2, "cantidad_elegida": 3 }
```
`cantidad_elegida` es `null` mientras el anfitrion no eligio todavia.

## Cliente → servidor (lobby)

### `elegir_cantidad`
Solo lo procesa el servidor si lo manda el anfitrion actual del lobby en el
que esta. Si alcanza la cantidad de gente conectada, arranca la partida de
inmediato (a los que sobran les llega un nuevo `esperando`/`elegir` para el
siguiente lobby).
```json
{ "type": "elegir_cantidad", "cantidad": 3 }
```
`cantidad` tiene que ser 2, 3 o 4; cualquier otro valor se ignora.

## Servidor → cliente (partida)

### `inicio`
Se manda a todos los jugadores de la partida cuando arranca.
```json
{
  "type": "inicio",
  "numero": 1,
  "campo": { "ancho": 1000, "alto": 1000 },
  "vertices": [[500, 70], [872.4, 715], [127.6, 715]],
  "bordes": [
    { "a": [500, 70], "b": [872.4, 715], "angulo": 1.05 },
    { "a": [872.4, 715], "b": [127.6, 715], "angulo": 3.14 },
    { "a": [127.6, 715], "b": [500, 70], "angulo": -1.05 }
  ],
  "jugador_bordes": [0, 1, 2],
  "pala": { "largo": 104, "grosor": 12 },
  "bola": { "tam": 12 },
  "poder_tam": 20,
  "vidas_iniciales": 3,
  "cantidad_jugadores": 3
}
```
`numero` es 1 a `cantidad_jugadores`, segun el orden de conexion.
`jugador_bordes[i]` es el indice de `bordes`/`vertices` que defiende el
jugador `i+1` (el jugador 1 defiende `bordes[jugador_bordes[0]]`, etc). Con 3
o 4 jugadores coincide siempre con `i` (`jugador_bordes` es `[0,1,2]` o
`[0,1,2,3]`); con 2 jugadores el campo tiene 4 bordes y solo 2 son de
jugador, asi que `jugador_bordes` puede ser, por ejemplo, `[3, 1]` — el
cliente **siempre** tiene que usar este mapeo en vez de asumir
`jugador_bordes[i] == i`. Cualquier indice de borde que no aparezca en
`jugador_bordes` es una pared fija desde el arranque (arriba/abajo del
rectangulo de 2 jugadores): el cliente la puede dibujar distinta (por
ejemplo, sin marca de jugador) porque nunca va a tener pala ni vidas.
`angulo` (en radianes) es el angulo de la tangente del borde — el cliente lo
usa para rotar el rectangulo de la pala al dibujarla, no hace falta que
calcule nada de trigonometria el mismo.

### `estado`
Se manda a todos los jugadores en cada tick del servidor (60 veces por
segundo mientras la partida esta activa).
```json
{
  "type": "estado",
  "bolas": [
    { "x": 494.0, "y": 510.5 }
  ],
  "palas": [
    { "x": 630.1, "y": 350.4, "largo": 104.0, "eliminado": false },
    { "x": 550.0, "y": 715.0, "largo": 166.4, "eliminado": false },
    { "x": 280.0, "y": 480.0, "largo": 104.0, "eliminado": true }
  ],
  "vidas": [3, 2, 0],
  "obstaculos": [
    { "x": 420.0, "y": 450.0, "ancho": 24, "alto": 74 },
    { "x": 560.0, "y": 520.0, "ancho": 24, "alto": 74 }
  ],
  "saque": false,
  "cuenta_saque": 3,
  "terminada": false,
  "ganador": null,
  "poderes": [
    { "tipo": "crecer", "simbolo": "+", "color": "#4ade80", "x": 512.0, "y": 480.0 },
    { "tipo": "paralisis", "simbolo": "Zz", "color": "#818cf8", "x": 450.0, "y": 520.0 }
  ],
  "empujon": [1.0, 0.4, 1.0],
  "impulso_color": null,
  "eventos": []
}
```
- `bolas`: normalmente una sola, pero el poder "multibola" puede sumar hasta
  `MULTIBOLA_MAX_BOLAS` (3 por defecto). Cualquier bola que se le escape a un
  jugador por donde su pala no cubre le cuesta una vida — con varias bolas en
  juego, perder cualquiera de ellas limpia todas las demas y se vuelve a
  sacar con una sola (para que el estado nunca quede a medio camino entre
  "una bola menos" y "sigue habiendo dos").
- `palas` tiene siempre `cantidad_jugadores` elementos: `palas[i]` es la pala
  del jugador `i+1`, en su propio borde (`bordes[jugador_bordes[i]]` de
  `inicio`) — **no** una entrada por borde geometrico (con 2 jugadores el
  campo tiene 4 bordes pero `palas` solo tiene 2). `x`/`y` es el **centro**
  de la pala en coordenadas del campo, ya rotado/desplazado (incluye el
  offset del empujon si esta en pleno dash) — el cliente solo la dibuja ahi,
  rotada segun el `angulo` de su borde, no hace ninguna cuenta. Si
  `eliminado` es `true`, ese borde paso a ser pared fija: el cliente la
  puede pintar distinto (gris/apagada) para marcar que ese jugador ya
  perdio.
- `vidas[i]`: vidas restantes del jugador `i+1`.
- `obstaculos`: bloques que rebotan solos, confinados a un cuadrado central
  (cabe en las 3 formas posibles del campo).
- `saque`/`cuenta_saque`: cuenta atras antes de cada saque (arranque de
  partida o despues de perder una vida).
- Cuando `terminada` es `true`, `ganador` es el numero (1 a
  `cantidad_jugadores`) del ultimo jugador con vidas, y ese es el ultimo
  `estado` que se manda.
- `poderes`: lista (puede estar vacia). Pueden convivir varios en el campo a
  la vez — cada tanto aparece uno nuevo sin importar si los anteriores
  siguen sin agarrar, hasta un tope (`PODER_MAX_SIMULTANEOS`, 4 por defecto).
  Tipos posibles: `crecer`, `encoger`, `veloz`, `lenta`, mas:
  - `multibola`: agrega bolas extra (clonadas de la que lo toco, con la
    velocidad rotada un poco para cada lado).
  - `empujon_libre`: durante `duracion` segundos, el empujon de quien lo
    agarro ignora el tiempo de espera normal — solo lo limita el tiempo que
    tarda la animacion de ida y vuelta (~0.3s), asi que se puede encadenar
    seguido.
  - `paralisis`: a un rival al azar (no a quien lo agarro) le reduce mucho
    la velocidad de su pala por `duracion` segundos, y a la vez frena la
    bola (mismo factor que el poder `lenta`) para que el paralizado tenga
    alguna chance real de todos modos.
  Los 7 tipos funcionan igual sin importar la cantidad de jugadores.
- `empujon[i]`: 0 a 1, que tan listo esta el empujon del jugador `i+1`
  (1 tambien durante un `empujon_libre` activo, aunque el cooldown de fondo
  siga corriendo).
- `impulso_color`: mientras no sea `null`, pinta la bola con ese color en
  vez del color normal del tema. Con varias bolas en juego (multibola) es
  una simplificacion deliberada: pinta **todas** las bolas del mismo color
  mientras dura, no solo la que efectivamente esta potenciada (el servidor
  solo le acelera la velocidad a esa una, pero distinguir cual es cual
  visualmente hubiera sumado bastante mas complejidad para un efecto que
  dura 3 segundos).
- `eventos`: particulas/sonido puntuales:
  - `{"tipo": "particulas", "x": .., "y": .., "color": .., "cantidad": ..}` —
    `color` es un hex fijo o una clave de tema (`"pala1"`..`"pala4"` segun
    `cantidad_jugadores`, o `"acento"`) que el cliente resuelve contra su
    paleta local.
  - `{"tipo": "sonido", "frecuencia": .., "duracion": ..}` — duracion en ms.

### `rival_desconectado`
Se manda a los jugadores que quedan si alguno de la partida cierra la
conexion (termina la partida para todos, no sigue entre los que quedan).
```json
{ "type": "rival_desconectado" }
```

## Cliente → servidor (partida)

### `input`
Se manda solo cuando el estado de una tecla cambia.
```json
{ "type": "input", "tecla": "arriba", "presionada": true }
```
`tecla` es `"arriba"` o `"abajo"`: mueve la pala hacia el extremo `a` o `b`
de tu borde (ver `bordes` en `inicio`), no es literalmente "arriba de la
pantalla" salvo para el jugador cuyo borde sea horizontal.

### `accion`
Un disparo puntual (el empujon), una vez por keydown de Shift.
```json
{ "type": "accion", "accion": "empujon" }
```

### `mouse`
Posicion cruda del cursor en coordenadas del campo (0 a `campo.ancho` /
`campo.alto`). El servidor la proyecta sobre el borde de ese jugador —
el cliente no sabe nada de bordes ni hace ninguna proyeccion.
```json
{ "type": "mouse", "x": 412.3, "y": 300.1 }
```
Sin limite de velocidad: la pala salta directo a la proyeccion. Mandar
`input` (de nuevo, cualquier tecla) devuelve el control al teclado hasta el
proximo mensaje `mouse`.
