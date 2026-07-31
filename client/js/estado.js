// Estado compartido del partido en curso. Nadie calcula fisica con esto:
// es una copia de lo ultimo que mando el servidor, que dibujo.js solo lee
// para pintar el cuadro actual.

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

export let ultimoEstado = null;

export function setUltimoEstado(estado) {
  ultimoEstado = estado;
}

export let miNumero = null;

export function setMiNumero(numero) {
  miNumero = numero;
}
