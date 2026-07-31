// Punto de entrada: conecta el socket, arranca el bucle de dibujo, y cablea
// cada modulo con el resto. No tiene logica propia -- si algo de lo de aca
// abajo crece, el lugar correcto es su propio modulo, no este archivo.
import { iniciarPanelAjustes } from "./ajustes.js";
import { actualizarMusica } from "./musica.js";
import { TEMAS } from "./temas.js";
import { iniciarBucle } from "./dibujo.js";
import { iniciarEntrada } from "./entrada.js";
import { iniciarLobby, manejarElegir, manejarEsperando } from "./lobby.js";
import { manejarEstado, manejarInicio, manejarRivalDesconectado } from "./juego.js";
import { conectar } from "./red.js";

iniciarPanelAjustes({
  temas: TEMAS,
  alCambiar: (clave) => {
    if (clave === "musica") actualizarMusica();
  },
});

iniciarLobby();
iniciarEntrada();
iniciarBucle();

conectar({
  elegir: manejarElegir,
  esperando: manejarEsperando,
  inicio: manejarInicio,
  estado: manejarEstado,
  rival_desconectado: manejarRivalDesconectado,
});
