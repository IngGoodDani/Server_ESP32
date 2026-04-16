// main.js - Punto de entrada de la aplicación

import { API_URL, STREAM_INTERVAL } from './constants.js';
import { initEventListeners, updateCamTimestamp } from './ui.js';
import { initGraphs } from './graphs.js';
import { ws_fetchData, checkHybridSystemStatus } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Aplicación iniciada - Sistema Híbrido SQLite + PostgreSQL');
  console.log('📡 API URL:', API_URL);

  initEventListeners();
  initGraphs();
  startDataFetching();
  updateCamTimestamp();
  setInterval(updateCamTimestamp, 1000);

  // Verificar estado del sistema híbrido
  checkHybridSystemStatus();
});

function startDataFetching() {
  console.log('🔄 Iniciando actualización automática de datos');
  ws_fetchData();
  //setInterval(ws_fetchData, STREAM_INTERVAL);
}