// Cliente de Pong online. Solo dibuja lo que el servidor manda: no calcula
// fisica ni colisiones ni decide reglas. Poderes/empujon/impulso son estado
// autoritativo del servidor; particulas/estela/sonido son 100% cosmeticos y
// reaccionan a los "eventos" que manda el servidor, pero viven y se animan
// aca nomas (el servidor no sabe ni le importa si hay una particula en pantalla).

// ---------------------------------------------------------------------------
// Temas — copia de las paletas de pong/temas.py. Es una preferencia local de
// cada jugador (como el ajustes.json del juego de escritorio), no algo que
// el servidor necesite conocer.
// ---------------------------------------------------------------------------
const TEMAS = [
  { nombre: "Neon", fondo: "#05070d", campo: "#0d1424", borde: "#1e2b47", linea: "#243354",
    pala_izq: "#22d3ee", pala_der: "#f472b6", bola: "#fde047", texto: "#e8eef7", tenue: "#5b6b87", acento: "#22d3ee" },
  { nombre: "Retro", fondo: "#000000", campo: "#04140a", borde: "#0f3d22", linea: "#124d1f",
    pala_izq: "#39ff14", pala_der: "#39ff14", bola: "#b6ff9e", texto: "#39ff14", tenue: "#1c6b2c", acento: "#39ff14" },
  { nombre: "Clasico", fondo: "#000000", campo: "#000000", borde: "#3a3a3a", linea: "#4a4a4a",
    pala_izq: "#ffffff", pala_der: "#ffffff", bola: "#ffffff", texto: "#ffffff", tenue: "#6e6e6e", acento: "#ffffff" },
  { nombre: "Atardecer", fondo: "#160b22", campo: "#241036", borde: "#4a2065", linea: "#5b2a7a",
    pala_izq: "#ff9e57", pala_der: "#ff5c8a", bola: "#ffe066", texto: "#f7e9ff", tenue: "#8b6ba8", acento: "#ff9e57" },
  { nombre: "Oceano", fondo: "#02121a", campo: "#062a3a", borde: "#0d4f66", linea: "#12657f",
    pala_izq: "#7dd3fc", pala_der: "#5eead4", bola: "#f0fdfa", texto: "#dff6ff", tenue: "#4a8ba3", acento: "#5eead4" },
  { nombre: "Papel", fondo: "#e8e2d4", campo: "#f5f1e8", borde: "#c9c0ac", linea: "#cfc6b2",
    pala_izq: "#c2410c", pala_der: "#1d4ed8", bola: "#1c1917", texto: "#292524", tenue: "#a8a29e", acento: "#c2410c" },
];

function mezclar(colorA, colorB, t) {
  t = Math.max(0, Math.min(1, t));
  const a = [1, 3, 5].map((i) => parseInt(colorA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(colorB.slice(i, i + 2), 16));
  const canal = (i) => Math.round(a[i] + (b[i] - a[i]) * t);
  return `#${canal(0).toString(16).padStart(2, "0")}${canal(1).toString(16).padStart(2, "0")}${canal(2).toString(16).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Ajustes: persistidos en localStorage, equivalente al ajustes.json del
// juego de escritorio pero por navegador en vez de por instalacion.
// ---------------------------------------------------------------------------
const CLAVE_AJUSTES = "pong-online-ajustes";
const AJUSTES_POR_DEFECTO = { tema: 0, brillo: true, estela: true, particulas: true, scanlines: false, sonido: true };

function cargarAjustes() {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE_AJUSTES));
    return { ...AJUSTES_POR_DEFECTO, ...guardado };
  } catch {
    return { ...AJUSTES_POR_DEFECTO };
  }
}

function guardarAjustes() {
  try {
    localStorage.setItem(CLAVE_AJUSTES, JSON.stringify(ajustes));
  } catch {
    // localStorage puede fallar (modo privado, cuota llena); no es critico.
  }
}

const ajustes = cargarAjustes();

function temaActual() {
  return TEMAS[ajustes.tema] || TEMAS[0];
}

function resolverColorEvento(color) {
  if (color.startsWith("#")) return color;
  const t = temaActual();
  if (color === "pala1") return t.pala_izq;
  if (color === "pala2") return t.pala_der;
  if (color === "bola") return t.bola;
  if (color === "acento") return t.acento;
  return t.texto;
}

// --- UI de ajustes -----------------------------------------------------
const selectTema = document.getElementById("ajuste-tema");
TEMAS.forEach((tema, indice) => {
  const opcion = document.createElement("option");
  opcion.value = String(indice);
  opcion.textContent = tema.nombre;
  selectTema.appendChild(opcion);
});
selectTema.value = String(ajustes.tema);
selectTema.addEventListener("change", () => {
  ajustes.tema = Number(selectTema.value);
  guardarAjustes();
});

function conectarCheckbox(id, clave) {
  const el = document.getElementById(id);
  el.checked = ajustes[clave];
  el.addEventListener("change", () => {
    ajustes[clave] = el.checked;
    guardarAjustes();
  });
}
conectarCheckbox("ajuste-brillo", "brillo");
conectarCheckbox("ajuste-estela", "estela");
conectarCheckbox("ajuste-particulas", "particulas");
conectarCheckbox("ajuste-scanlines", "scanlines");
conectarCheckbox("ajuste-sonido", "sonido");

// ---------------------------------------------------------------------------
// Conexion y estado del juego
// ---------------------------------------------------------------------------
const lienzo = document.getElementById("campo");
const ctx = lienzo.getContext("2d");
const elementoMensaje = document.getElementById("mensaje");

let geometria = {
  campo: { ancho: 800, alto: 500 },
  pala: { ancho: 12, alto: 82, margen: 34 },
  bola: { tam: 12 },
  poder_tam: 20,
  puntos_para_ganar: 7,
};

let miNumero = null;
let ultimoEstado = null;

const protocolo = location.protocol === "https:" ? "wss:" : "ws:";
const socket = new WebSocket(`${protocolo}//${location.host}/ws`);

function enviarMensaje(objeto) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(objeto));
  }
}

function mostrarMensaje(texto, esAviso = false) {
  elementoMensaje.textContent = texto;
  elementoMensaje.classList.toggle("aviso", esAviso);
}

socket.addEventListener("open", () => mostrarMensaje("Conectado. Buscando oponente..."));
socket.addEventListener("close", () => mostrarMensaje("Se perdio la conexion con el servidor.", true));
socket.addEventListener("error", () => mostrarMensaje("No se pudo conectar al servidor.", true));

socket.addEventListener("message", (evento) => {
  const mensaje = JSON.parse(evento.data);
  switch (mensaje.type) {
    case "esperando":
      mostrarMensaje("Esperando a un oponente...");
      break;

    case "inicio":
      geometria = {
        campo: mensaje.campo,
        pala: mensaje.pala,
        bola: mensaje.bola,
        poder_tam: mensaje.poder_tam,
        puntos_para_ganar: mensaje.puntos_para_ganar,
      };
      miNumero = mensaje.numero;
      lienzo.width = geometria.campo.ancho;
      lienzo.height = geometria.campo.alto;
      mostrarMensaje(
        `Arranco la partida. Sos el jugador ${miNumero} (${miNumero === 1 ? "izquierda" : "derecha"}).`
      );
      break;

    case "estado":
      ultimoEstado = mensaje;
      if (mensaje.saque) {
        estela.length = 0;
      } else {
        agregarEstela(mensaje.bola.x, mensaje.bola.y);
      }
      for (const ev of mensaje.eventos) {
        if (ev.tipo === "particulas") {
          emitirParticulas(ev.x, ev.y, ev.color, ev.cantidad);
        } else if (ev.tipo === "sonido") {
          pitido(ev.frecuencia, ev.duracion);
        }
      }
      break;

    case "rival_desconectado":
      mostrarMensaje("El otro jugador se desconecto.", true);
      break;

    default:
      // Tipo de mensaje que este cliente todavia no conoce: se ignora, asi
      // el protocolo puede crecer sin romper clientes viejos.
      break;
  }
});

// ---------------------------------------------------------------------------
// Particulas (cosmeticas, disparadas por los "eventos" del servidor)
// ---------------------------------------------------------------------------
const MAX_PARTICULAS = 120;
let particulas = [];

function emitirParticulas(x, y, colorClave, cantidad) {
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

function actualizarParticulas() {
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

function dibujarParticulas() {
  const t = temaActual();
  for (const p of particulas) {
    const proporcion = p.vida / p.vidaMax;
    const tam = 1 + 2.6 * proporcion;
    rect(p.x - tam, p.y - tam, tam * 2, tam * 2, mezclar(p.color, t.campo, 1 - proporcion));
  }
}

// ---------------------------------------------------------------------------
// Estela de la bola
// ---------------------------------------------------------------------------
const LARGO_ESTELA = 14;
let estela = [];

function colorBolaActual() {
  if (ultimoEstado && ultimoEstado.impulso_color) return ultimoEstado.impulso_color;
  return temaActual().bola;
}

function agregarEstela(x, y) {
  estela.push({ x, y });
  if (estela.length > LARGO_ESTELA) estela.shift();
}

function dibujarEstela() {
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

// ---------------------------------------------------------------------------
// Sonido: beeps sintetizados con Web Audio (no hay winsound en un navegador).
// Los navegadores bloquean audio hasta el primer gesto del usuario, por eso
// el AudioContext se crea recien en el primer keydown/click.
// ---------------------------------------------------------------------------
let audioCtx = null;

function asegurarAudio() {
  if (!audioCtx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    audioCtx = new Ctx();
  } else if (audioCtx.state === "suspended") {
    audioCtx.resume();
  }
}
window.addEventListener("keydown", asegurarAudio, { once: true });
window.addEventListener("click", asegurarAudio, { once: true });

function pitido(frecuencia, duracionMs) {
  if (!ajustes.sonido || !audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = "square";
  osc.frequency.value = Math.max(37, Math.min(20000, frecuencia));
  osc.connect(gain);
  gain.connect(audioCtx.destination);

  const ahora = audioCtx.currentTime;
  const duracionSeg = duracionMs / 1000;
  gain.gain.setValueAtTime(0.06, ahora);
  gain.gain.exponentialRampToValueAtTime(0.0001, ahora + duracionSeg);
  osc.start(ahora);
  osc.stop(ahora + duracionSeg);
}

// ---------------------------------------------------------------------------
// Input: flechas (estado sostenido) + Shift (accion de un solo disparo)
// ---------------------------------------------------------------------------
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

// --- Control por mouse ---------------------------------------------------
// La pala sigue al mouse 1 a 1 (sin tope de velocidad) — el servidor la
// mueve directo a la posicion que le mandamos aca, no hay "persecucion" a
// velocidad fija como con el teclado. Mandar cualquier input de teclado
// hace que el servidor vuelva a usar el teclado para esa pala.
//
// Se manda desde el evento mousemove (no en un loop aparte) para no mandar
// nada mientras el mouse esta quieto, con un throttle simple para no
// inundar el socket si el navegador dispara mousemove muy seguido.
let ultimoEnvioMouseMs = 0;
const INTERVALO_MOUSE_MS = 16; // ~60 mensajes por segundo como mucho

lienzo.addEventListener("mousemove", (evento) => {
  const ahora = performance.now();
  if (ahora - ultimoEnvioMouseMs < INTERVALO_MOUSE_MS) return;
  ultimoEnvioMouseMs = ahora;

  const caja = lienzo.getBoundingClientRect();
  const escalaY = geometria.campo.alto / caja.height;
  const y = (evento.clientY - caja.top) * escalaY;
  enviarMensaje({ type: "mouse", y: Math.round(y * 10) / 10 });
});

// ---------------------------------------------------------------------------
// Dibujo
// ---------------------------------------------------------------------------
let reloj = 0; // frames locales, solo para animar (el pulso del poder)

function rect(x, y, ancho, alto, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, ancho, alto);
}

function rectConBrillo(x, y, ancho, alto, colorBase) {
  rect(x, y, ancho, alto, colorBase);
  if (!ajustes.brillo) return;
  const margenX = ancho * 0.22;
  const claro = mezclar(colorBase, "#ffffff", 0.55);
  const oscuro = mezclar(colorBase, "#000000", 0.35);
  rect(x + margenX, y + alto * 0.12, ancho - margenX * 2, alto * 0.30, claro);
  rect(x + margenX, y + alto * 0.70, ancho - margenX * 2, alto * 0.18, oscuro);
}

function dibujarCampo() {
  const t = temaActual();
  const { ancho, alto } = geometria.campo;
  rect(0, 0, ancho, alto, t.campo);
  ctx.strokeStyle = t.borde;
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, ancho - 2, alto - 2);
  for (let y = 0; y < alto; y += 32) {
    rect(ancho / 2 - 2, y + 7, 4, 18, t.linea);
  }
}

function dibujarPala(estadoPala, ancho, color, esLaMia) {
  // estadoPala.x refleja la posicion real del servidor, incluido el
  // desplazamiento del empujon — no un x fijo calculado de "inicio".
  rectConBrillo(estadoPala.x, estadoPala.y, ancho, estadoPala.alto, color);
  if (esLaMia) {
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.strokeRect(estadoPala.x - 2, estadoPala.y - 2, ancho + 4, estadoPala.alto + 4);
  }
}

function dibujarObstaculos() {
  const t = temaActual();
  const color = mezclar(t.tenue, t.texto, 0.25);
  for (const o of ultimoEstado.obstaculos) {
    rectConBrillo(o.x, o.y, o.ancho, o.alto, color);
  }
}

function dibujarBola() {
  const tam = geometria.bola.tam;
  rectConBrillo(ultimoEstado.bola.x, ultimoEstado.bola.y, tam, tam, colorBolaActual());
}

function dibujarMarcador() {
  const t = temaActual();
  const { ancho } = geometria.campo;
  ctx.textAlign = "center";
  ctx.font = "bold 44px Consolas, monospace";
  ctx.fillStyle = t.pala_izq;
  ctx.fillText(String(ultimoEstado.marcador[0]), ancho / 2 - 70, 58);
  ctx.fillStyle = t.pala_der;
  ctx.fillText(String(ultimoEstado.marcador[1]), ancho / 2 + 70, 58);
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

function dibujarIndicadorEmpujon(proporcion, color, lado) {
  const t = temaActual();
  const { ancho: campoAncho, alto: campoAlto } = geometria.campo;
  const anchoBarra = 34;
  const altoBarra = 5;
  const y = campoAlto - 16;
  const x = lado === "izq"
    ? geometria.pala.margen
    : campoAncho - geometria.pala.margen - anchoBarra;

  rect(x, y, anchoBarra, altoBarra, mezclar(color, t.campo, 0.75));
  const relleno = proporcion >= 1 ? color : mezclar(color, t.campo, 0.35);
  const ancho = anchoBarra * proporcion;
  if (lado === "izq") {
    rect(x, y, ancho, altoBarra, relleno);
  } else {
    rect(x + anchoBarra - ancho, y, ancho, altoBarra, relleno);
  }
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

  if (!ultimoEstado) {
    if (ajustes.scanlines) dibujarScanlines();
    return;
  }

  const t = temaActual();

  dibujarMarcador();
  dibujarObstaculos();
  if (ajustes.particulas) dibujarParticulas();
  if (ajustes.estela) dibujarEstela();
  if (ultimoEstado.poder) dibujarPoder(ultimoEstado.poder);

  dibujarPala(ultimoEstado.pala1, geometria.pala.ancho, t.pala_izq, miNumero === 1);
  dibujarPala(ultimoEstado.pala2, geometria.pala.ancho, t.pala_der, miNumero === 2);

  dibujarIndicadorEmpujon(ultimoEstado.empujon1, t.pala_izq, "izq");
  dibujarIndicadorEmpujon(ultimoEstado.empujon2, t.pala_der, "der");

  if (!ultimoEstado.terminada) {
    dibujarBola();
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
    ctx.fillText(String(ultimoEstado.cuenta_saque), geometria.campo.ancho / 2, geometria.campo.alto / 2 + 78);
  }

  if (ajustes.scanlines) dibujarScanlines();
}

function cuadro() {
  reloj += 1;
  actualizarParticulas();
  dibujar();
  requestAnimationFrame(cuadro);
}
requestAnimationFrame(cuadro);
