// Musica de fondo: un loop corto generado con Web Audio (mismo criterio que
// audio.js -- nada de archivos para descargar, todo sintetizado en el
// momento). Un bajo suave y un arpegio arriba, en La menor, dando vueltas
// cada 16 pasos. Va bastante mas bajo de volumen que los efectos (0.06 en
// audio.js) para no taparlos ni cansar en partidas largas.
import { ajustes } from "./ajustes.js";
import { obtenerContexto } from "./audio.js";

const BPM = 96;
const PASO_SEG = 60 / BPM / 2; // corcheas
const ANTICIPACION_SEG = 0.12; // cuanto planifica el planificador hacia adelante
const INTERVALO_PLANIFICADOR_MS = 40;

const VOLUMEN = 0.026; // notablemente mas bajo que el pitido de efectos (0.06)

// Progresion Am - F - C - G, arpegiada de a 4 notas por acorde (16 pasos).
const A2 = 110.0, F2 = 87.31, C3 = 130.81, G2 = 98.0;
const A3 = 220.0, C4 = 261.63, D4 = 293.66, E4 = 329.63, F3 = 174.61, F4 = 349.23,
  G3 = 196.0, G4 = 392.0, B3 = 246.94, A4 = 440.0, C5 = 523.25;

const BAJO = [A2, null, null, null, F2, null, null, null, C3, null, null, null, G2, null, null, null];
const ARPEGIO = [A3, C4, E4, A4, F3, A3, C4, F4, C4, E4, G4, C5, G3, B3, D4, G4];

let ganancia = null;
let filtro = null;
let idIntervalo = null;
let siguientePaso = 0;
let siguienteTiempo = 0;

function asegurarGrafo(contexto) {
  if (ganancia) return;
  filtro = contexto.createBiquadFilter();
  filtro.type = "lowpass";
  filtro.frequency.value = 2200;
  ganancia = contexto.createGain();
  ganancia.gain.value = VOLUMEN;
  filtro.connect(ganancia);
  ganancia.connect(contexto.destination);
}

function tocarNota(contexto, frecuencia, inicio, duracion, tipo) {
  if (!frecuencia) return;
  const osc = contexto.createOscillator();
  const envolvente = contexto.createGain();
  osc.type = tipo;
  osc.frequency.value = frecuencia;
  osc.connect(envolvente);
  envolvente.connect(filtro);
  envolvente.gain.setValueAtTime(0, inicio);
  envolvente.gain.linearRampToValueAtTime(1, inicio + 0.02);
  envolvente.gain.exponentialRampToValueAtTime(0.0001, inicio + duracion);
  osc.start(inicio);
  osc.stop(inicio + duracion + 0.05);
}

function planificar(contexto) {
  while (siguienteTiempo < contexto.currentTime + ANTICIPACION_SEG) {
    const paso = siguientePaso % ARPEGIO.length;
    tocarNota(contexto, ARPEGIO[paso], siguienteTiempo, PASO_SEG * 0.85, "triangle");
    tocarNota(contexto, BAJO[paso], siguienteTiempo, PASO_SEG * 3.6, "sine");
    siguienteTiempo += PASO_SEG;
    siguientePaso += 1;
  }
}

function estaSonando() {
  return idIntervalo !== null;
}

function iniciar(contexto) {
  if (estaSonando()) return;
  asegurarGrafo(contexto);
  siguientePaso = 0;
  siguienteTiempo = contexto.currentTime + 0.05;
  planificar(contexto);
  idIntervalo = setInterval(() => planificar(contexto), INTERVALO_PLANIFICADOR_MS);
}

function detener() {
  if (idIntervalo !== null) {
    clearInterval(idIntervalo);
    idIntervalo = null;
  }
}

/** Prende o apaga el loop segun `ajustes.musica`. Sin efecto si todavia no
 * hay AudioContext (nadie hizo el primer gesto que lo desbloquea). Se llama
 * al arrancar y cada vez que el usuario toca el checkbox de "Musica". */
export function actualizarMusica() {
  const contexto = obtenerContexto();
  if (!contexto || !ajustes.musica) {
    detener();
    return;
  }
  iniciar(contexto);
}
