// Input: flechas (estado sostenido, mueve a lo largo de tu borde) + Shift
// (empujon, un solo disparo por keydown) + mouse (sigue al cursor 1 a 1).
// El primer gesto (keydown o click) tambien desbloquea el audio del
// navegador y arranca la musica de fondo si corresponde.
import { asegurarContexto } from "./audio.js";
import { geometria } from "./estado.js";
import { lienzo } from "./lienzo.js";
import { actualizarMusica } from "./musica.js";
import { enviarMensaje } from "./red.js";

function primerGesto() {
  asegurarContexto();
  actualizarMusica();
}

const teclas = { arriba: false, abajo: false };
let empujonPresionado = false;

function enviarInput(tecla, presionada) {
  if (teclas[tecla] === presionada) return;
  teclas[tecla] = presionada;
  enviarMensaje({ type: "input", tecla, presionada });
}

function rolDeTecla(codigo) {
  if (codigo === "ArrowUp") return "arriba";
  if (codigo === "ArrowDown") return "abajo";
  return null;
}

function esTeclaEmpujon(codigo) {
  return codigo === "ShiftLeft" || codigo === "ShiftRight";
}

export function iniciarEntrada() {
  window.addEventListener("keydown", primerGesto, { once: true });
  window.addEventListener("click", primerGesto, { once: true });

  window.addEventListener("keydown", (evento) => {
    const rol = rolDeTecla(evento.code);
    if (rol) {
      evento.preventDefault();
      enviarInput(rol, true);
      return;
    }
    if (esTeclaEmpujon(evento.code)) {
      evento.preventDefault();
      if (!empujonPresionado) {
        empujonPresionado = true;
        enviarMensaje({ type: "accion", accion: "empujon" });
      }
    }
  });

  window.addEventListener("keyup", (evento) => {
    const rol = rolDeTecla(evento.code);
    if (rol) {
      evento.preventDefault();
      enviarInput(rol, false);
      return;
    }
    if (esTeclaEmpujon(evento.code)) {
      empujonPresionado = false;
    }
  });

  // Si la pestana pierde el foco con una tecla apretada, el keyup nunca llega.
  window.addEventListener("blur", () => {
    enviarInput("arriba", false);
    enviarInput("abajo", false);
    empujonPresionado = false;
  });

  // Se manda la posicion cruda del cursor (en coordenadas del campo); el
  // servidor la proyecta sobre el borde de cada jugador. El cliente no sabe
  // nada de bordes ni de proyecciones, solo manda donde esta el mouse.
  let ultimoEnvioMouseMs = 0;
  const INTERVALO_MOUSE_MS = 16; // ~60 mensajes por segundo como mucho

  lienzo.addEventListener("mousemove", (evento) => {
    const ahora = performance.now();
    if (ahora - ultimoEnvioMouseMs < INTERVALO_MOUSE_MS) return;
    ultimoEnvioMouseMs = ahora;

    const caja = lienzo.getBoundingClientRect();
    const escalaX = geometria.campo.ancho / caja.width;
    const escalaY = geometria.campo.alto / caja.height;
    const x = (evento.clientX - caja.left) * escalaX;
    const y = (evento.clientY - caja.top) * escalaY;
    enviarMensaje({ type: "mouse", x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 });
  });
}
