// Traduce los mensajes de partida (`inicio`, `estado`, `rival_desconectado`)
// a cambios en el estado compartido (estado.js) y a los efectos puntuales
// que disparan: sonido y particulas. dibujo.js se encarga de pintar el
// resultado en los cuadros siguientes; este modulo no dibuja nada.
import { pitido } from "./audio.js";
import { ajustarTamanoLienzo } from "./dibujo.js";
import { emitirParticulas } from "./efectos.js";
import { registrarEstado, setGeometria, setMiNumero } from "./estado.js";
import { ocultarLobby } from "./lobby.js";
import { mostrarMensaje } from "./ui.js";

export function manejarInicio(mensaje) {
  ocultarLobby();
  setGeometria({
    campo: mensaje.campo,
    vertices: mensaje.vertices,
    bordes: mensaje.bordes,
    jugador_bordes: mensaje.jugador_bordes,
    cantidad_jugadores: mensaje.cantidad_jugadores,
    pala: mensaje.pala,
    bola: mensaje.bola,
    poder_tam: mensaje.poder_tam,
    vidas_iniciales: mensaje.vidas_iniciales,
  });
  setMiNumero(mensaje.numero);
  ajustarTamanoLienzo();
  mostrarMensaje(`Arranco la partida. Sos el jugador ${mensaje.numero}.`);
}

export function manejarEstado(mensaje) {
  registrarEstado(mensaje);
  // La estela no se alimenta aca sino en el bucle de dibujo: tiene que
  // seguir la posicion *interpolada* de la bola (la que se ve realmente),
  // porque si no la cola quedaria adelantada respecto de la bola.
  for (const ev of mensaje.eventos) {
    if (ev.tipo === "particulas") {
      emitirParticulas(ev.x, ev.y, ev.color, ev.cantidad);
    } else if (ev.tipo === "sonido") {
      pitido(ev.frecuencia, ev.duracion);
    }
  }
}

export function manejarRivalDesconectado() {
  mostrarMensaje("Otro jugador se desconecto. Se termino la partida.", true);
}
