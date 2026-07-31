// Suavizado del movimiento entre estados del servidor.
//
// El servidor manda ~60 estados por segundo, pero el navegador dibuja a la
// tasa de tu monitor (60, 120, 144Hz...) y los paquetes llegan con jitter de
// red. Dibujar siempre el ultimo estado recibido significa que cuando un
// paquete se demora se pinta la misma posicion dos cuadros seguidos y
// despues salta el doble: eso son los micro-tirones.
//
// La solucion es dibujar en el punto intermedio entre los dos ultimos
// estados, segun cuanto tiempo real paso desde que llego el ultimo. El
// costo es que se dibuja ~un cuadro de servidor "en el pasado" (~17ms).
// Es despreciable al lado del viaje de ida y vuelta hasta el servidor
// (~50-150ms) que ya existe de todos modos, y a cambio saca todos los
// tirones. Se interpola todo por igual (incluida tu propia pala) a
// proposito: hacer una excepcion con la tuya la dejaria saltando mientras
// el resto se mueve suave, que se nota mas que los 17ms.

import {
  estadoPrevio,
  llegadaPrevio,
  llegadaUltimo,
  ultimoEstado,
} from "./estado.js";

// Topes de cordura para el periodo medido entre paquetes: si el servidor
// hipa o el navegador estuvo en segundo plano, el intervalo medido puede ser
// absurdo y arruinar la cuenta.
const PERIODO_MIN_MS = 8;
const PERIODO_MAX_MS = 100;

function interpolarLista(listaPrevia, listaActual, t, campos) {
  // Si cambio la cantidad de elementos no hay correspondencia 1-a-1 confiable
  // entre indices (paso un multibola, se perdio una vida, aparecio o se
  // agarro un poder): se usa el estado nuevo tal cual.
  if (!listaPrevia || !listaActual || listaPrevia.length !== listaActual.length) {
    return listaActual;
  }
  return listaActual.map((itemActual, i) => {
    const itemPrevio = listaPrevia[i];
    const salida = { ...itemActual };
    for (const campo of campos) {
      salida[campo] = itemPrevio[campo] + (itemActual[campo] - itemPrevio[campo]) * t;
    }
    return salida;
  });
}

/** El estado a dibujar en este cuadro: el ultimo recibido, con las posiciones
 * movidas hacia el punto que corresponde al tiempo real transcurrido. */
export function estadoParaDibujar() {
  if (!ultimoEstado) return null;
  if (!estadoPrevio) return ultimoEstado; // recien llego el primero

  const periodo = Math.min(
    PERIODO_MAX_MS,
    Math.max(PERIODO_MIN_MS, llegadaUltimo - llegadaPrevio)
  );
  // Se acota a 1: si el proximo paquete se demora mas de lo normal, se queda
  // quieto en la ultima posicion conocida en vez de inventar uno futuro que
  // despues habria que corregir hacia atras.
  const t = Math.min(1, (performance.now() - llegadaUltimo) / periodo);

  return {
    ...ultimoEstado,
    // Durante el saque la bola se teletransporta al centro: interpolar eso
    // la mostraria volando desde donde se escapo hasta el medio.
    bolas: ultimoEstado.saque
      ? ultimoEstado.bolas
      : interpolarLista(estadoPrevio.bolas, ultimoEstado.bolas, t, ["x", "y"]),
    // `largo` tambien se interpola: hace que crecer/encoger por un poder se
    // vea como una animacion en vez de un salto.
    palas: interpolarLista(estadoPrevio.palas, ultimoEstado.palas, t, ["x", "y", "largo"]),
    obstaculos: interpolarLista(estadoPrevio.obstaculos, ultimoEstado.obstaculos, t, ["x", "y"]),
  };
}
