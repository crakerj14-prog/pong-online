// Efectos cosmeticos disparados por los "eventos" del servidor o por el
// movimiento de la bola: particulas puntuales y la estela que deja atras.
// Ninguno de los dos influye en el juego -- si se desactivan en Ajustes, no
// cambia nada de lo que ve el servidor.
import { ajustes } from "./ajustes.js";
import { geometria, ultimoEstado } from "./estado.js";
import { rect } from "./lienzo.js";
import { mezclar, resolverColorEvento, temaActual } from "./temas.js";

// --- Particulas --------------------------------------------------------
const MAX_PARTICULAS = 120;
let particulas = [];

export function emitirParticulas(x, y, colorClave, cantidad) {
  if (!ajustes.particulas) return;
  const color = resolverColorEvento(colorClave);
  const libres = MAX_PARTICULAS - particulas.length;
  const n = Math.min(cantidad, Math.max(0, libres));
  for (let i = 0; i < n; i++) {
    const angulo = Math.random() * Math.PI * 2;
    const rapidez = 0.8 + Math.random() * 2.6;
    const vida = 14 + Math.floor(Math.random() * 17);
    particulas.push({
      x, y,
      vx: Math.cos(angulo) * rapidez,
      vy: Math.sin(angulo) * rapidez,
      vida, vidaMax: vida,
      color,
    });
  }
}

export function actualizarParticulas() {
  particulas = particulas.filter((p) => {
    p.vida -= 1;
    if (p.vida <= 0) return false;
    p.x += p.vx;
    p.y += p.vy;
    p.vy += 0.08;
    p.vx *= 0.97;
    return true;
  });
}

export function dibujarParticulas() {
  const t = temaActual();
  for (const p of particulas) {
    const proporcion = p.vida / p.vidaMax;
    const tam = 1 + 2.6 * proporcion;
    rect(p.x - tam, p.y - tam, tam * 2, tam * 2, mezclar(p.color, t.campo, 1 - proporcion));
  }
}

// --- Estela de la bola ---------------------------------------------------
const LARGO_ESTELA = 14;
let estela = [];

export function colorBolaActual() {
  if (ultimoEstado && ultimoEstado.impulso_color) return ultimoEstado.impulso_color;
  return temaActual().bola;
}

export function agregarEstela(x, y) {
  estela.push({ x, y });
  if (estela.length > LARGO_ESTELA) estela.shift();
}

export function limpiarEstela() {
  estela.length = 0;
}

export function dibujarEstela() {
  const total = estela.length;
  if (total < 2) return;
  const t = temaActual();
  const tam = geometria.bola.tam;
  const colorBase = colorBolaActual();
  estela.forEach((punto, indice) => {
    const proporcion = (indice + 1) / total;
    const mitad = (tam * (0.35 + 0.65 * proporcion)) / 2;
    const cx = punto.x + tam / 2;
    const cy = punto.y + tam / 2;
    rect(cx - mitad, cy - mitad, mitad * 2, mitad * 2, mezclar(colorBase, t.campo, 1 - proporcion * 0.75));
  });
}
