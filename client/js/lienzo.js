// El <canvas> y las primitivas de dibujo mas basicas, compartidas por
// dibujo.js (campo, palas, bolas...) y efectos.js (particulas, estela).
import { ajustes } from "./ajustes.js";
import { mezclar } from "./temas.js";

export const lienzo = document.getElementById("campo");
export const ctx = lienzo.getContext("2d");

export function rect(x, y, ancho, alto, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, ancho, alto);
}

export function rectConBrillo(x, y, ancho, alto, colorBase) {
  rect(x, y, ancho, alto, colorBase);
  if (!ajustes.brillo) return;
  const margenX = ancho * 0.22;
  const claro = mezclar(colorBase, "#ffffff", 0.55);
  const oscuro = mezclar(colorBase, "#000000", 0.35);
  rect(x + margenX, y + alto * 0.12, ancho - margenX * 2, alto * 0.30, claro);
  rect(x + margenX, y + alto * 0.70, ancho - margenX * 2, alto * 0.18, oscuro);
}
