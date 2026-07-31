// Efectos de sonido: beeps sintetizados con Web Audio (no hay winsound en
// un navegador, y asi no dependemos de ningun archivo de audio). Los
// navegadores bloquean audio hasta el primer gesto del usuario, por eso el
// AudioContext se crea recien cuando alguien lo pide explicitamente (ver
// `asegurarContexto`, llamado desde entrada.js en el primer keydown/click).
import { ajustes } from "./ajustes.js";

let contexto = null;

export function asegurarContexto() {
  if (!contexto) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    contexto = new Ctx();
  } else if (contexto.state === "suspended") {
    contexto.resume();
  }
  return contexto;
}

export function obtenerContexto() {
  return contexto;
}

export function pitido(frecuencia, duracionMs) {
  if (!ajustes.sonido || !contexto) return;
  const osc = contexto.createOscillator();
  const gain = contexto.createGain();
  osc.type = "square";
  osc.frequency.value = Math.max(37, Math.min(20000, frecuencia));
  osc.connect(gain);
  gain.connect(contexto.destination);

  const ahora = contexto.currentTime;
  const duracionSeg = duracionMs / 1000;
  gain.gain.setValueAtTime(0.06, ahora);
  gain.gain.exponentialRampToValueAtTime(0.0001, ahora + duracionSeg);
  osc.start(ahora);
  osc.stop(ahora + duracionSeg);
}
