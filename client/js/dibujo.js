// Todo el dibujo en <canvas>. No calcula fisica ni reglas: solo lee
// `geometria`/`ultimoEstado` (estado.js) y los pinta. El bucle de
// requestAnimationFrame tambien vive aca, porque es puramente de
// presentacion (anima particulas y el pulso de los poderes aunque no haya
// llegado un `estado` nuevo en ese cuadro).
import { ajustes } from "./ajustes.js";
import {
  actualizarParticulas,
  colorBolaActual,
  dibujarEstela,
  dibujarParticulas,
} from "./efectos.js";
import { ctx, lienzo, rect, rectConBrillo } from "./lienzo.js";
import { geometria, miNumero, ultimoEstado } from "./estado.js";
import { mezclar, temaActual } from "./temas.js";

let reloj = 0; // frames locales, solo para animar (el pulso del poder)

function dibujarCampo() {
  const t = temaActual();
  const { ancho, alto } = geometria.campo;
  rect(0, 0, ancho, alto, t.fondo);
  if (!geometria.vertices) return;

  ctx.fillStyle = t.campo;
  ctx.beginPath();
  ctx.moveTo(geometria.vertices[0][0], geometria.vertices[0][1]);
  for (let i = 1; i < geometria.vertices.length; i++) {
    ctx.lineTo(geometria.vertices[i][0], geometria.vertices[i][1]);
  }
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = t.borde;
  ctx.lineWidth = 3;
  ctx.stroke();

  ctx.fillStyle = t.linea;
  ctx.beginPath();
  ctx.arc(ancho / 2, alto / 2, 5, 0, Math.PI * 2);
  ctx.fill();
}

function dibujarPalaTriangular(indiceBorde, indiceJugador, estadoPala, colorTema) {
  const borde = geometria.bordes[indiceBorde];
  const t = temaActual();
  const grosor = geometria.pala.grosor;
  const color = estadoPala.eliminado ? mezclar(t.tenue, t.campo, 0.25) : colorTema;

  ctx.save();
  ctx.translate(estadoPala.x, estadoPala.y);
  ctx.rotate(borde.angulo);
  rectConBrillo(-estadoPala.largo / 2, -grosor / 2, estadoPala.largo, grosor, color);
  if (miNumero === indiceJugador + 1 && !estadoPala.eliminado) {
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.strokeRect(-estadoPala.largo / 2 - 2, -grosor / 2 - 2, estadoPala.largo + 4, grosor + 4);
  }
  ctx.restore();
}

function normalDeBorde(indice) {
  const angulo = geometria.bordes[indice].angulo;
  return [-Math.sin(angulo), Math.cos(angulo)];
}

function dibujarInfoJugador(indice, colorTema, vidas, proporcionEmpujon, eliminado) {
  const borde = geometria.bordes[indice];
  const mx = (borde.a[0] + borde.b[0]) / 2;
  const my = (borde.a[1] + borde.b[1]) / 2;
  const [nx, ny] = normalDeBorde(indice);
  // -normal: hacia afuera del campo (la normal del servidor apunta hacia adentro).
  const px = mx - nx * 36;
  const py = my - ny * 36;
  const t = temaActual();

  if (eliminado) {
    ctx.textAlign = "center";
    ctx.font = "12px Consolas, monospace";
    ctx.fillStyle = t.tenue;
    ctx.fillText("eliminado", px, py);
    return;
  }

  const radioVida = 5;
  const espacio = 14;
  const inicioX = px - ((vidas - 1) * espacio) / 2;
  for (let i = 0; i < vidas; i++) {
    ctx.fillStyle = colorTema;
    ctx.beginPath();
    ctx.arc(inicioX + i * espacio, py, radioVida, 0, Math.PI * 2);
    ctx.fill();
  }

  const anchoBarra = 40;
  const altoBarra = 4;
  const bx = px - anchoBarra / 2;
  const by = py + 14;
  rect(bx, by, anchoBarra, altoBarra, mezclar(colorTema, t.campo, 0.75));
  const relleno = proporcionEmpujon >= 1 ? colorTema : mezclar(colorTema, t.campo, 0.35);
  rect(bx, by, anchoBarra * proporcionEmpujon, altoBarra, relleno);
}

function dibujarObstaculos() {
  const t = temaActual();
  const color = mezclar(t.tenue, t.texto, 0.25);
  for (const o of ultimoEstado.obstaculos) {
    rectConBrillo(o.x, o.y, o.ancho, o.alto, color);
  }
}

function dibujarBolas() {
  const tam = geometria.bola.tam;
  // Simplificacion deliberada: todas las bolas usan el mismo color de
  // impulso mientras dure, aunque el servidor solo le haya acelerado la
  // velocidad a la que efectivamente conecto el golpe potenciado (ver
  // PROTOCOLO.md).
  const color = colorBolaActual();
  for (const bola of ultimoEstado.bolas) {
    rectConBrillo(bola.x, bola.y, tam, tam, color);
  }
}

function dibujarPoder(poder) {
  const t = temaActual();
  const r = geometria.poder_tam / 2;
  const respiro = 3 + 3 * (0.5 + 0.5 * Math.sin(reloj * 0.1));

  for (const [extra, mezcla] of [[respiro + 7, 0.85], [respiro + 3, 0.65]]) {
    ctx.fillStyle = mezclar(poder.color, t.campo, mezcla);
    ctx.beginPath();
    ctx.arc(poder.x, poder.y, r + extra, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = poder.color;
  ctx.beginPath();
  ctx.arc(poder.x, poder.y, r, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#10141c";
  ctx.font = "bold 12px Consolas, monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(poder.simbolo, poder.x, poder.y);
  ctx.textBaseline = "alphabetic";
}

function dibujarPanel(titulo, subtitulo) {
  const t = temaActual();
  const { ancho, alto } = geometria.campo;
  rect(ancho / 2 - 255, alto / 2 - 62, 510, 124, mezclar(t.campo, t.fondo, 0.6));

  ctx.fillStyle = t.texto;
  ctx.textAlign = "center";
  ctx.font = "bold 30px Consolas, monospace";
  ctx.fillText(titulo, ancho / 2, alto / 2 - 10);

  ctx.font = "13px Consolas, monospace";
  ctx.fillStyle = t.tenue;
  ctx.fillText(subtitulo, ancho / 2, alto / 2 + 22);
}

function dibujarScanlines() {
  const t = temaActual();
  const { ancho, alto } = geometria.campo;
  ctx.strokeStyle = mezclar(t.campo, "#000000", 0.45);
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let y = 0; y < alto; y += 4) {
    ctx.moveTo(0, y);
    ctx.lineTo(ancho, y);
  }
  ctx.stroke();
}

function dibujar() {
  dibujarCampo();

  if (!ultimoEstado || !geometria.bordes) {
    if (ajustes.scanlines) dibujarScanlines();
    return;
  }

  const t = temaActual();
  const coloresPala = [t.pala1, t.pala2, t.pala3, t.pala4];
  const cantidadJugadores = geometria.cantidad_jugadores || ultimoEstado.palas.length;

  dibujarObstaculos();
  if (ajustes.particulas) dibujarParticulas();
  if (ajustes.estela) dibujarEstela();
  for (const poder of ultimoEstado.poderes) {
    dibujarPoder(poder);
  }

  for (let i = 0; i < cantidadJugadores; i++) {
    const indiceBorde = geometria.jugador_bordes[i];
    dibujarPalaTriangular(indiceBorde, i, ultimoEstado.palas[i], coloresPala[i]);
  }
  for (let i = 0; i < cantidadJugadores; i++) {
    const indiceBorde = geometria.jugador_bordes[i];
    dibujarInfoJugador(indiceBorde, coloresPala[i], ultimoEstado.vidas[i], ultimoEstado.empujon[i], ultimoEstado.palas[i].eliminado);
  }

  if (!ultimoEstado.terminada) {
    dibujarBolas();
  }

  if (ultimoEstado.terminada) {
    const gano = ultimoEstado.ganador === miNumero;
    dibujarPanel(
      gano ? "GANASTE" : `Jugador ${ultimoEstado.ganador} gana`,
      "Recarga la pagina para jugar otra vez"
    );
  } else if (ultimoEstado.saque) {
    ctx.fillStyle = t.acento;
    ctx.font = "bold 26px Consolas, monospace";
    ctx.textAlign = "center";
    ctx.fillText(String(ultimoEstado.cuenta_saque), geometria.campo.ancho / 2, geometria.campo.alto / 2 + 40);
  }

  if (ajustes.scanlines) dibujarScanlines();
}

export function iniciarBucle() {
  function cuadro() {
    reloj += 1;
    actualizarParticulas();
    dibujar();
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(cuadro);
}

export function ajustarTamanoLienzo() {
  lienzo.width = geometria.campo.ancho;
  lienzo.height = geometria.campo.alto;
}
