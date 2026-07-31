// El cartel de estado ("Conectando...", "Arranco la partida", etc). Lo usan
// tanto el lobby como el juego en curso, asi que vive en su propio modulo
// chico en vez de en cualquiera de los dos.

const elementoMensaje = document.getElementById("mensaje");

export function mostrarMensaje(texto, esAviso = false) {
  elementoMensaje.textContent = texto;
  elementoMensaje.classList.toggle("aviso", esAviso);
}
