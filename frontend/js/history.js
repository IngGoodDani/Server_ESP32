// history.js - Funciones para la vista de historial (CAM view y línea de tiempo)

import { variables, colors, WINDOW_SIZE, genericOptions } from './constants.js';
import { getState, setState } from './state.js';

export function displayHistoricalWindow(startIndex) {
  const { selectedMeasurementData, camCharts } = getState();
  if (!selectedMeasurementData || selectedMeasurementData.length === 0) return;

  const maxStart = Math.max(0, selectedMeasurementData.length - WINDOW_SIZE);
  startIndex = Math.max(0, Math.min(startIndex, maxStart));
  setState({ currentSliderPosition: startIndex });

  const slider = document.getElementById('timelineSlider');
  if (slider) slider.value = startIndex;

  const windowEnd = Math.min(startIndex + WINDOW_SIZE, selectedMeasurementData.length);
  safeSetTextContent('timelinePosition', startIndex);
  safeSetTextContent('windowEnd', windowEnd);

  const windowData = selectedMeasurementData.slice(startIndex, windowEnd);

  const container = document.getElementById('camViewGrid');

  // Si no hay gráficas creadas, crearlas
  if (Object.keys(camCharts).length === 0) {
    container.innerHTML = '';

    variables.forEach(variable => {
      const monitor = document.createElement('div');
      monitor.className = 'cam-monitor';
      monitor.innerHTML = `
        <h4>📡 ${variable}</h4>
        <canvas id="cam-chart-${variable}"></canvas>
      `;
      container.appendChild(monitor);

      const ctx = document.getElementById(`cam-chart-${variable}`).getContext('2d');
      camCharts[variable] = new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: variable,
            data: [],
            borderColor: colors[variable],
            backgroundColor: colors[variable] + '20',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4
          }]
        },
        options: genericOptions
      });
    });
    setState({ camCharts });
  }

  // Actualizar gráficas
  variables.forEach(variable => {
    const chart = camCharts[variable];
    if (!chart) return;

    chart.data.labels = windowData.map((_, i) => startIndex + i);
    chart.data.datasets[0].data = windowData.map(d => d[variable] || 0);
    chart.update('none');
  });
}

// Helper (repetido aquí para evitar dependencia circular)
function safeSetTextContent(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) element.textContent = value;
}