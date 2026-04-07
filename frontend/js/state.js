// state.js - Estado global de la aplicación

import { WINDOW_SIZE } from './constants.js';

// Estado centralizado
const state = {
  // Datos en tiempo real
  data: [],
  realtimeData: null,
  predictions: null,
  showPredictions: false,
  isRecording: false,
  activeTab: 'graphs',
  graphMode: 'all',
  charts: {},
  singleChart: null,
  comparisonChart: null,

  // Sistema híbrido
  lastSampleId: 0,
  allMeasurements: [],
  selectedMeasurementId: null,
  selectedMeasurementNumSamples: null,
  selectedMeasurementData: [],
  currentSliderPosition: 0,
  playbackInterval: null,
  camCharts: {},
  autoUpdateHistory: false,

  // IA
  predictionHorizon: 50,
  isPredicting: false,

  // Streaming
  isStreaming: false,
  streamInterval: null,

  // Paginación
  currentPage: 1,
  totalPages: 1,
  totalSamples: 0,

  // Cache local
  localCache: {
    recentData: [],
    lastUpdate: 0,
    cacheDuration: 2000
  },

  // Estado del sistema híbrido
  systemStatus: {
    hybridEnabled: false,
    cacheSamples: 0,
    postgresSamples: 0
  },

  // Banderas
  chargeHybridSystem: false,
  
  // Graficas
  MAX_POINTS: 100,
  
  // Medición
  samplingTime: 20
};

// Getters y setters (opcional, se puede acceder directamente)
export function getState() {
  return state;
}

export function setState(newState) {
  Object.assign(state, newState);
}

// Exportar propiedades individuales para facilitar importación
export const data = () => state.data;
export const setData = (newData) => { state.data = newData; };
// ... se pueden agregar más según necesidad