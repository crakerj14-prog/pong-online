# Protocolo WebSocket

Todos los mensajes son JSON con un campo `"type"`. Conexion en `/ws`.

## Servidor → cliente

### `esperando`
Se manda apenas te conectas, si todavia no hay un segundo jugador.
```json
{ "type": "esperando" }
```

### `inicio`
Se manda a los dos jugadores cuando se completa el emparejamiento. Trae toda
la geometria del campo: el cliente no tiene ningun tamano hardcodeado, dibuja
lo que el servidor le diga.
```json
{
  "type": "inicio",
  "numero": 1,
  "campo": { "ancho": 800, "alto": 500 },
  "pala": { "ancho": 12, "alto": 82, "margen": 34 },
  "bola": { "tam": 12 },
  "poder_tam": 20,
  "puntos_para_ganar": 7
}
```
`numero` es 1 (pala izquierda) o 2 (pala derecha), segun el orden de conexion.

### `estado`
Se manda a los dos jugadores en cada tick del servidor (60 veces por segundo
mientras la partida esta activa).
```json
{
  "type": "estado",
  "bola": { "x": 394.0, "y": 210.5 },
  "pala1": { "x": 34.0, "y": 209.0, "alto": 82.0 },
  "pala2": { "x": 754.0, "y": 250.3, "alto": 131.2 },
  "marcador": [2, 1],
  "saque": false,
  "cuenta_saque": 3,
  "terminada": false,
  "ganador": null,
  "poder": { "tipo": "crecer", "simbolo": "+", "color": "#4ade80", "x": 412.0, "y": 260.0 },
  "empujon1": 1.0,
  "empujon2": 0.42,
  "impulso_color": null,
  "eventos": []
}
```
- `pala1`/`pala2`: la pala 1 arranca a la izquierda, la 2 a la derecha, pero
  `x` **si puede cambiar**: el empujon mueve la pala en X durante el dash. El
  `alto` tambien varia cuando un poder agranda o encoge la pala. El cliente
  tiene que dibujar la pala en el `x`/`y`/`alto` que le llega en cada
  `estado`, no en valores fijos calculados a partir de `inicio`.
- `saque` es `true` durante la cuenta atras antes de cada saque; `cuenta_saque`
  es el numero (3, 2, 1) para mostrar mientras tanto.
- Cuando `terminada` pasa a `true`, `ganador` es `1` o `2` y ese es el ultimo
  mensaje `estado` que se manda para esa partida.
- `poder` es `null` si no hay ningun poder esperando en el campo ahora mismo.
- `empujon1`/`empujon2`: 0 a 1, que tan listo esta el empujon de cada jugador
  (1 = listo para usar). Para dibujar la barrita de cooldown.
- `impulso_color` es `null` salvo mientras la bola esta en el pico de
  velocidad de un golpe potenciado (ver `eventos` de tipo `sonido` con
  frecuencia 900 para saber cuando empezo). Mientras no sea `null`, dibuja la
  bola con ese color en vez del color normal del tema.
- `eventos`: lista de cosas puntuales que pasaron desde el `estado` anterior
  (normalmente vacia; puede traer varios si coincide mas de una cosa en el
  mismo cuadro). Dos tipos:
  - `{"tipo": "particulas", "x": .., "y": .., "color": .., "cantidad": ..}` —
    `color` es un hex fijo (`"#rrggbb"`) **o** una clave de tema
    (`"pala1"`, `"pala2"`, `"bola"`, `"acento"`) que el cliente resuelve
    contra su propia paleta local. El servidor no sabe que tema tiene elegido
    cada jugador — por eso las claves en vez de colores fijos para todo.
  - `{"tipo": "sonido", "frecuencia": .., "duracion": ..}` — duracion en ms.

### `rival_desconectado`
Se manda al jugador que queda si el otro cierra la conexion.
```json
{ "type": "rival_desconectado" }
```

## Cliente → servidor

### `input`
Se manda solo cuando el estado de una tecla cambia (no en cada evento de
auto-repeat del sistema operativo).
```json
{ "type": "input", "tecla": "arriba", "presionada": true }
```
`tecla` es `"arriba"` o `"abajo"`. `presionada` es `true` en keydown, `false`
en keyup (o al perder el foco de la ventana).

### `accion`
Un disparo puntual, no un estado sostenido — se manda una vez por keydown de
la tecla de empujon (Shift), nunca en el keyup ni en auto-repeat.
```json
{ "type": "accion", "accion": "empujon" }
```
El servidor ignora el mensaje si el empujon de ese jugador todavia esta en
cooldown (no revienta ni contesta error, simplemente no pasa nada).
