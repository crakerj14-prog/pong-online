// Ajustes: preferencia local de cada jugador, persistida en localStorage
// (el equivalente web del ajustes.json del juego de escritorio). El
// servidor no sabe que ajustes tiene puesto cada uno.

const CLAVE_AJUSTES = "pong-online-ajustes";
const POR_DEFECTO = {
  tema: 0,
  brillo: true,
  estela: true,
  particulas: true,
  scanlines: false,
  sonido: true,
  musica: true,
};

function cargar() {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE_AJUSTES));
    return { ...POR_DEFECTO, ...guardado };
  } catch {
    return { ...POR_DEFECTO };
  }
}

export const ajustes = cargar();

export function guardarAjustes() {
  try {
    localStorage.setItem(CLAVE_AJUSTES, JSON.stringify(ajustes));
  } catch {
    // localStorage puede fallar (modo privado, cuota llena); no es critico.
  }
}

/** Conecta el panel de "Ajustes" del HTML (select de tema + checkboxes) al
 * objeto `ajustes`, y dispara `alCambiar` cada vez que el usuario toca algo
 * (por ejemplo, para prender/apagar la musica de fondo en el momento). */
export function iniciarPanelAjustes({ temas, alCambiar }) {
  const selectTema = document.getElementById("ajuste-tema");
  temas.forEach((tema, indice) => {
    const opcion = document.createElement("option");
    opcion.value = String(indice);
    opcion.textContent = tema.nombre;
    selectTema.appendChild(opcion);
  });
  selectTema.value = String(ajustes.tema);
  selectTema.addEventListener("change", () => {
    ajustes.tema = Number(selectTema.value);
    guardarAjustes();
    alCambiar?.("tema");
  });

  function conectarCheckbox(id, clave) {
    const el = document.getElementById(id);
    el.checked = ajustes[clave];
    el.addEventListener("change", () => {
      ajustes[clave] = el.checked;
      guardarAjustes();
      alCambiar?.(clave);
    });
  }
  conectarCheckbox("ajuste-brillo", "brillo");
  conectarCheckbox("ajuste-estela", "estela");
  conectarCheckbox("ajuste-particulas", "particulas");
  conectarCheckbox("ajuste-scanlines", "scanlines");
  conectarCheckbox("ajuste-sonido", "sonido");
  conectarCheckbox("ajuste-musica", "musica");
}
