// Conexion WebSocket con el servidor. No sabe nada de reglas del juego: solo
// abre el socket, manda JSON, y reparte cada mensaje entrante al manejador
// que le corresponda segun su "type" (ver PROTOCOLO.md). Si no hay manejador
// para un tipo, se ignora solo -- asi el protocolo puede crecer sin romper
// clientes viejos.
import { mostrarMensaje } from "./ui.js";

let socket = null;

export function enviarMensaje(objeto) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(objeto));
  }
}

export function conectar(manejadores) {
  const protocolo = location.protocol === "https:" ? "wss:" : "ws:";
  socket = new WebSocket(`${protocolo}//${location.host}/ws`);

  socket.addEventListener("open", () => mostrarMensaje("Conectado. Buscando jugadores..."));
  socket.addEventListener("close", () => mostrarMensaje("Se perdio la conexion con el servidor.", true));
  socket.addEventListener("error", () => mostrarMensaje("No se pudo conectar al servidor.", true));

  socket.addEventListener("message", (evento) => {
    const mensaje = JSON.parse(evento.data);
    const manejador = manejadores[mensaje.type];
    if (manejador) manejador(mensaje);
  });
}
