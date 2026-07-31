// UI del lobby: los botones 2/3/4 que solo ve el anfitrion (el primero en
// conectarse), y el texto de espera que ven los demas. Traduce los mensajes
// `elegir`/`esperando` del servidor (ver PROTOCOLO.md) a esos elementos, y
// manda `elegir_cantidad` cuando el anfitrion aprieta un boton.
import { enviarMensaje } from "./red.js";
import { mostrarMensaje } from "./ui.js";

const lobbyOpciones = document.getElementById("lobby-opciones");
const botonesCantidad = Array.from(document.querySelectorAll(".btn-cantidad"));

export function iniciarLobby() {
  botonesCantidad.forEach((boton) => {
    boton.addEventListener("click", () => {
      if (boton.disabled) return;
      enviarMensaje({ type: "elegir_cantidad", cantidad: Number(boton.dataset.cantidad) });
    });
  });
}

export function manejarElegir(mensaje) {
  lobbyOpciones.classList.remove("oculto");
  botonesCantidad.forEach((boton) => {
    const cantidad = Number(boton.dataset.cantidad);
    boton.disabled = mensaje.conectados < cantidad;
    boton.classList.toggle("activo", mensaje.cantidad_elegida === cantidad);
  });
  mostrarMensaje(
    mensaje.cantidad_elegida
      ? `Sos el anfitrion. Conectados: ${mensaje.conectados}. Esperando a ${mensaje.cantidad_elegida} jugadores.`
      : `Sos el anfitrion. Conectados: ${mensaje.conectados}. Elegi cuantos van a jugar.`
  );
}

export function manejarEsperando(mensaje) {
  lobbyOpciones.classList.add("oculto");
  mostrarMensaje(
    mensaje.cantidad_elegida
      ? `Conectados: ${mensaje.conectados}. El anfitrion eligio ${mensaje.cantidad_elegida} jugadores.`
      : `Conectados: ${mensaje.conectados}. Esperando a que el anfitrion elija cuantos van a jugar.`
  );
}

export function ocultarLobby() {
  lobbyOpciones.classList.add("oculto");
}
