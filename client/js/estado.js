// Estado compartido del partido en curso. Nadie calcula fisica con esto:
// es una copia de lo que mando el servidor.
//
// Se guardan los DOS ultimos estados recibidos (con el momento en que
// llegaron) porque el cliente dibuja mas seguido de lo que el servidor
// manda: interpolacion.js los mezcla para producir el cuadro intermedio.
// Para leer algo que no sea una posicion (impulso_color, vidas, si termino)
// alcanza y sobra con `ultimoEstado`.

export let geometria = {
  campo: { ancho: 800, alto: 800 },
  vertices: null,
  bordes: null,
  jugador_bordes: null,
  cantidad_jugadores: null,
  pala: { largo: 82, grosor: 12 },
  bola: { tam: 12 },
  poder_tam: 20,
  vidas_iniciales: 3,
};

export function setGeometria(nueva) {
  geometria = nueva;
}

export let ultimoEstado = null;      // el mas reciente que llego
export let estadoPrevio = null;      // el anterior a ese
export let llegadaUltimo = 0;        // performance.now() de cada uno
export let llegadaPrevio = 0;

export function registrarEstado(estado) {
  estadoPrevio = ultimoEstado;
  llegadaPrevio = llegadaUltimo;
  ultimoEstado = estado;
  llegadaUltimo = performance.now();
}

export let miNumero = null;

export function setMiNumero(numero) {
  miNumero = numero;
}
