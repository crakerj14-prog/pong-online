// Cliente de Pong (2 a 4 jugadores, elegido por el anfitrion en el lobby).
// Solo dibuja lo que el servidor manda: no calcula fisica, colisiones, ni
// vidas. Poderes/empujon/impulso son estado autoritativo del servidor;
// particulas/estela/sonido son 100% cosmeticos y reaccionan a los "eventos"
// que manda el servidor, pero viven y se animan aca nomas.

// ---------------------------------------------------------------------------
// Temas — paletas de color, preferencia local de cada jugador (localStorage,
// el equivalente web del ajustes.json de escritorio). El servidor no sabe
// que tema tiene puesto cada uno. `pala4` solo se usa en partidas de 4.
// ---------------------------------------------------------------------------
const TEMAS = [
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

function mezclar(colorA, colorB, t) {
  t = Math.max(0, Math.min(1, t));
  const a = [1, 3, 5].map((i) => parseInt(colorA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(colorB.slice(i, i + 2), 16));
  const canal = (i) => Math.round(a[i] + (b[i] - a[i]) * t);
  return `#${canal(0).toString(16).padStart(2, "0")}${canal(1).toString(16).padStart(2, "0")}${canal(2).toString(16).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Ajustes: persistidos en localStorage.
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
  if (color === "pala1") return t.pala1;
  if (color === "pala2") return t.pala2;
  if (color === "pala3") return t.pala3;
  if (color === "pala4") return t.pala4;
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
  campo: { ancho: 800, alto: 800 },
  vertices: null,
  bordes: null,
  jugador_bordes: null,
  cantidad_jugadores: null,
  pala: { largo: 82, grosor: 12 },
  bola: { tam: 12 },
  poder_tam: 20,
  vidas_iniciales: 3,
};

let miNumero = null;
let ultimoEstado = null;

// --- UI del lobby (eleccion de cantidad de jugadores) ---------------------
const lobbyOpciones = document.getElementById("lobby-opciones");
const botonesCantidad = Array.from(document.querySelectorAll(".btn-cantidad"));
botonesCantidad.forEach((boton) => {
  boton.addEventListener("click", () => {
    if (boton.disabled) return;
    enviarMensaje({ type: "elegir_cantidad", cantidad: Number(boton.dataset.cantidad) });
  });
});

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

socket.addEventListener("open", () => mostrarMensaje("Conectado. Buscando jugadores..."));
socket.addEventListener("close", () => mostrarMensaje("Se perdio la conexion con el servidor.", true));
socket.addEventListener("error", () => mostrarMensaje("No se pudo conectar al servidor.", true));

socket.addEventListener("message", (evento) => {
  const mensaje = JSON.parse(evento.data);
  switch (mensaje.type) {
    case "elegir": {
      lobbyOpciones.classList.remove("oculto");
      botonesCantidad.forEach((boton) => {
        const cantidad = Number(boton.dataset.cantidad);
        boton.disabled = mensaje.conectados < cantidad;
        boton.classList.toggle("activo", mensaje.cantidad_elegida === cantidad);
      });
      mostrarMensaje(
        mensaje.cantidad_elegida
          ? `Sos el anfitrion. Conectados: ${mensaje.conectados}. Esperando a ${mensaje.cantidad_elegida} jugadores.`
          : `Sos el anfitrion. Conectados: ${mensaje.conectados}. Elegi cuantos van a jugar.`
      );
      break;
    }

    case "esperando":
      lobbyOpciones.classList.add("oculto");
      mostrarMensaje(
        mensaje.cantidad_elegida
          ? `Conectados: ${mensaje.conectados}. El anfitrion eligio ${mensaje.cantidad_elegida} jugadores.`
          : `Conectados: ${mensaje.conectados}. Esperando a que el anfitrion elija cuantos van a jugar.`
      );
      break;

    case "inicio":
      lobbyOpciones.classList.add("oculto");
      geometria = {
        campo: mensaje.campo,
        vertices: mensaje.vertices,
        bordes: mensaje.bordes,
        jugador_bordes: mensaje.jugador_bordes,
        cantidad_jugadores: mensaje.cantidad_jugadores,
        pala: mensaje.pala,
        bola: mensaje.bola,
        poder_tam: mensaje.poder_tam,
        vidas_iniciales: mensaje.vidas_iniciales,
      };
      miNumero = mensaje.numero;
      lienzo.width = geometria.campo.ancho;
      lienzo.height = geometria.campo.alto;
      mostrarMensaje(`Arranco la partida. Sos el jugador ${miNumero}.`);
      break;

    case "estado":
      ultimoEstado = mensaje;
      if (mensaje.saque || mensaje.bolas.length === 0) {
        estela.length = 0;
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
      break;

    case "rival_desconectado":
      mostrarMensaje("Otro jugador se desconecto. Se termino la partida.", true);
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
// Input: flechas (estado sostenido, mueve a lo largo de tu borde) + Shift
// (empujon, un solo disparo) + mouse (sigue al cursor 1 a 1).
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
  // -normal: hacia afuera del triangulo (la normal del servidor apunta hacia adentro).
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

function cuadro() {
  reloj += 1;
  actualizarParticulas();
  dibujar();
  requestAnimationFrame(cuadro);
}
requestAnimationFrame(cuadro);
