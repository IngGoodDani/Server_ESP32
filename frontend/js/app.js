// main.js - Punto de entrada de la aplicación

import { API_URL } from './constants.js';
import { initEventListeners, updateCamTimestamp } from './ui.js';
import { initGraphs } from './graphs.js';
import { fetchData, checkHybridSystemStatus } from './api.js';
import { STREAM_INTERVAL } from './constants.js';

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
  fetchData();
  setInterval(fetchData, STREAM_INTERVAL);
}