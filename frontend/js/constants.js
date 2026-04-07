// constants.js - Constantes globales de la aplicación

export const API_URL = window.location.origin;
//export let MAX_POINTS = 100;
export const STREAM_INTERVAL = 500;
export const WINDOW_SIZE = 200;
export const PAGE_SIZE = 1000;

export const variables = [
  'VoltajeEntrada', 'VoltajeDiodo', 'VoltajeSalida',
  'CorrienteEntrada', 'CorrienteInductor', 'CorrienteDiodo', 'CorrienteSalida',
  'PotenciaEntrada', 'PotenciaSalida'
];

export const colors = {
  VoltajeEntrada: '#3b82f6',
  VoltajeDiodo: '#8b5cf6',
  VoltajeSalida: '#10b981',
  CorrienteEntrada: '#f59e0b',
  CorrienteInductor: '#ef4444',
  CorrienteDiodo: '#ec4899',
  CorrienteSalida: '#06b6d4',
  PotenciaEntrada: '#989080',
  PotenciaSalida: '#0bb82a'
};

export const genericOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  scales: {
    x: {
      type: 'linear',
      title: { display: true, text: 'Tiempo' },
      grid: { color: '#404040' },
      ticks: { color: '#9ca3af' }
    },
    y: {
      type: 'linear',
      min: 0,
      display: true,
      grid: { color: '#404040' },
      ticks: { color: '#9ca3af' }
    }
  },
  plugins: {
    legend: {
      display: true,
      labels: { color: '#e5e7eb' }
    }
  }
};