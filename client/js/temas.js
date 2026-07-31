// Temas: paletas de color. `pala4` solo se usa en partidas de 4 jugadores
// (campo cuadrado); en las de 2 o 3 esos bordes ni existen.
import { ajustes } from "./ajustes.js";

export const TEMAS = [
  { nombre: "Neon", fondo: "#05070d", campo: "#0d1424", borde: "#1e2b47", linea: "#243354",
    pala1: "#22d3ee", pala2: "#f472b6", pala3: "#a3e635", pala4: "#c084fc", bola: "#fde047", texto: "#e8eef7", tenue: "#5b6b87", acento: "#22d3ee" },
  { nombre: "Retro", fondo: "#000000", campo: "#04140a", borde: "#0f3d22", linea: "#124d1f",
    pala1: "#39ff14", pala2: "#ffb000", pala3: "#00e5ff", pala4: "#ff2079", bola: "#b6ff9e", texto: "#39ff14", tenue: "#1c6b2c", acento: "#39ff14" },
  { nombre: "Clasico", fondo: "#000000", campo: "#000000", borde: "#3a3a3a", linea: "#4a4a4a",
    pala1: "#ffffff", pala2: "#f87171", pala3: "#60a5fa", pala4: "#facc15", bola: "#ffffff", texto: "#ffffff", tenue: "#6e6e6e", acento: "#ffffff" },
  { nombre: "Atardecer", fondo: "#160b22", campo: "#241036", borde: "#4a2065", linea: "#5b2a7a",
    pala1: "#ff9e57", pala2: "#ff5c8a", pala3: "#c084fc", pala4: "#2dd4bf", bola: "#ffe066", texto: "#f7e9ff", tenue: "#8b6ba8", acento: "#ff9e57" },
  { nombre: "Oceano", fondo: "#02121a", campo: "#062a3a", borde: "#0d4f66", linea: "#12657f",
    pala1: "#7dd3fc", pala2: "#5eead4", pala3: "#a78bfa", pala4: "#fb7185", bola: "#f0fdfa", texto: "#dff6ff", tenue: "#4a8ba3", acento: "#5eead4" },
  { nombre: "Papel", fondo: "#e8e2d4", campo: "#f5f1e8", borde: "#c9c0ac", linea: "#cfc6b2",
    pala1: "#c2410c", pala2: "#1d4ed8", pala3: "#15803d", pala4: "#7c3aed", bola: "#1c1917", texto: "#292524", tenue: "#a8a29e", acento: "#c2410c" },
];

export function mezclar(colorA, colorB, t) {
  t = Math.max(0, Math.min(1, t));
  const a = [1, 3, 5].map((i) => parseInt(colorA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(colorB.slice(i, i + 2), 16));
  const canal = (i) => Math.round(a[i] + (b[i] - a[i]) * t);
  return `#${canal(0).toString(16).padStart(2, "0")}${canal(1).toString(16).padStart(2, "0")}${canal(2).toString(16).padStart(2, "0")}`;
}

export function temaActual() {
  return TEMAS[ajustes.tema] || TEMAS[0];
}

export function resolverColorEvento(color) {
  if (color.startsWith("#")) return color;
  const t = temaActual();
  if (color === "pala1") return t.pala1;
  if (color === "pala2") return t.pala2;
  if (color === "pala3") return t.pala3;
  if (color === "pala4") return t.pala4;
  if (color === "bola") return t.bola;
  if (color === "acento") return t.acento;
  return t.texto;
}
