# Protocolo WebSocket

Todos los mensajes son JSON con un campo `"type"`. Conexion en `/ws`.

Modo triangular: 3 jugadores, cada uno defiende un lado del triangulo. El
campo es un cuadrado de `campo.ancho` x `campo.alto` con el triangulo
inscripto adentro; el servidor manda las coordenadas de los 3 vertices y
bordes una sola vez (en `inicio`) porque no cambian durante la partida.

## Servidor → cliente

### `esperando`
Se manda apenas te conectas, mientras falten jugadores para completar el trio.
```json
{ "type": "esperando", "conectados": 2, "necesarios": 3 }
```

### `inicio`
Se manda a los 3 jugadores cuando se completa el emparejamiento.
```json
{
  "type": "inicio",
  "numero": 1,
  "campo": { "ancho": 800, "alto": 800 },
  "vertices": [[400, 60], [694.4, 570], [105.6, 570]],
  "bordes": [
    { "a": [400, 60], "b": [694.4, 570], "angulo": 1.05 },
    { "a": [694.4, 570], "b": [105.6, 570], "angulo": 3.14 },
    { "a": [105.6, 570], "b": [400, 60], "angulo": -1.05 }
  ],
  "pala": { "largo": 82, "grosor": 12 },
  "bola": { "tam": 12 },
  "poder_tam": 20,
  "vidas_iniciales": 3
}
```
`numero` es 1, 2 o 3, segun el orden de conexion. `bordes[i]` es el borde que
defiende el jugador `i+1` (el jugador 1 defiende `bordes[0]`, etc). `angulo`
(en radianes) es el angulo de la tangente del borde — el cliente lo usa para
rotar el rectangulo de la pala al dibujarla, no hace falta que calcule nada
de trigonometria el mismo.

### `estado`
Se manda a los 3 jugadores en cada tick del servidor (60 veces por segundo
mientras la partida esta activa).
```json
{
  "type": "estado",
  "bolas": [
    { "x": 394.0, "y": 410.5 }
  ],
  "palas": [
    { "x": 500.1, "y": 280.4, "largo": 82.0, "eliminado": false },
    { "x": 450.0, "y": 570.0, "largo": 131.2, "eliminado": false },
    { "x": 150.0, "y": 400.0, "largo": 82.0, "eliminado": true }
  ],
  "vidas": [3, 2, 0],
  "obstaculos": [
    { "x": 320.0, "y": 350.0, "ancho": 20, "alto": 60 },
    { "x": 460.0, "y": 420.0, "ancho": 20, "alto": 60 }
  ],
  "saque": false,
  "cuenta_saque": 3,
  "terminada": false,
  "ganador": null,
  "poderes": [
    { "tipo": "crecer", "simbolo": "+", "color": "#4ade80", "x": 412.0, "y": 380.0 },
    { "tipo": "paralisis", "simbolo": "Zz", "color": "#818cf8", "x": 350.0, "y": 420.0 }
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
- `palas[i]` es la pala del jugador `i+1`. `x`/`y` es el **centro** de la
  pala en coordenadas del campo, ya rotado/desplazado (incluye el offset del
  empujon si esta en pleno dash) — el cliente solo la dibuja ahi, rotada
  segun el `angulo` de su borde (de `inicio`), no hace ninguna cuenta. Si
  `eliminado` es `true`, ese borde es pared fija: el cliente la puede pintar
  distinto (gris/apagada) para marcar que ese jugador ya perdio.
- `vidas[i]`: vidas restantes del jugador `i+1`.
- `obstaculos`: igual que en el modo de 2, bloques que rebotan solos (ahora
  confinados a un cuadrado central en vez de una franja).
- `saque`/`cuenta_saque`: igual que antes, cuenta atras antes de cada saque
  (arranque de partida o despues de perder una vida).
- Cuando `terminada` es `true`, `ganador` es el numero (1/2/3) del ultimo
  jugador con vidas, y ese es el ultimo `estado` que se manda.
- `poderes`: lista (puede estar vacia). Pueden convivir varios en el campo a
  la vez — cada tanto aparece uno nuevo sin importar si los anteriores
  siguen sin agarrar, hasta un tope (`PODER_MAX_SIMULTANEOS`, 4 por defecto).
  Los tipos posibles: `crecer`, `encoger`, `veloz`, `lenta` (ver el modo de
  2 jugadores) mas tres nuevos de este modo:
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
- `empujon[i]`: 0 a 1, que tan listo esta el empujon del jugador `i+1`
  (1 tambien durante un `empujon_libre` activo, aunque el cooldown de fondo
  siga corriendo).
- `impulso_color`: igual que el modo de 2 — mientras no sea `null`, pinta la
  bola con ese color en vez del color normal del tema. Con varias bolas en
  juego (multibola) es una simplificacion deliberada: pinta **todas** las
  bolas del mismo color mientras dura, no solo la que efectivamente esta
  potenciada (el servidor solo le acelera la velocidad a esa una, pero
  distinguir cual es cual visualmente hubiera sumado bastante mas
  complejidad para un efecto que dura 3 segundos).
- `eventos`: particulas/sonido puntuales, mismo formato que el modo de 2:
  - `{"tipo": "particulas", "x": .., "y": .., "color": .., "cantidad": ..}` —
    `color` es un hex fijo o una clave de tema (`"pala1"`, `"pala2"`,
    `"pala3"`, `"acento"`) que el cliente resuelve contra su paleta local.
  - `{"tipo": "sonido", "frecuencia": .., "duracion": ..}` — duracion en ms.

### `rival_desconectado`
Se manda a los jugadores que quedan si alguno de los 3 cierra la conexion
(termina la partida para todos, no sigue entre los 2 restantes).
```json
{ "type": "rival_desconectado" }
```

## Cliente → servidor

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
