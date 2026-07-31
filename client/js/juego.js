// Traduce los mensajes de partida (`inicio`, `estado`, `rival_desconectado`)
// a cambios en el estado compartido (estado.js) y a los efectos que
// disparan: sonido, particulas y la estela de la bola. dibujo.js se encarga
// de pintar el resultado en el cuadro siguiente; este modulo no dibuja nada.
import { pitido } from "./audio.js";
import { ajustarTamanoLienzo } from "./dibujo.js";
import { agregarEstela, emitirParticulas, limpiarEstela } from "./efectos.js";
import { setGeometria, setMiNumero, setUltimoEstado } from "./estado.js";
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
  setUltimoEstado(mensaje);
  if (mensaje.saque || mensaje.bolas.length === 0) {
    limpiarEstela();
  } else {
    // La estela solo sigue a la primera bola: con multibola activo las
    // demas no dejan rastro, para no complicar el sistema de estela con
    // varias colas independientes por un efecto que dura poco.
    agregarEstela(mensaje.bolas[0].x, mensaje.bolas[0].y);
  }
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
