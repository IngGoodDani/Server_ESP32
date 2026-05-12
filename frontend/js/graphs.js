// graphs.js - Creación y actualización de gráficas en tiempo real

import { variables, colors, genericOptions } from './constants.js';
import { getState, setState } from './state.js';
import { safeSetTextContent } from './ui.js';

export function initGraphs() {
  const container = document.getElementById('allGraphs');
  const charts = {};

  variables.forEach(variable => {
    const card = document.createElement('div');
    card.className = 'graph-card';
    const displayValue = 'N/A';
    card.innerHTML = `
      <h3>${variable}</h3>
      <span class="value"><span id="${variable}-value">${displayValue}</span></span>
      <div class="unit">${variable.includes('Corriente') ? 'Amperios' : variable.includes('Voltaje') ? 'Voltios' : 'Wats'}</div>
      <canvas id="chart-${variable}"></canvas>
    `;
    container.appendChild(card);

    const ctx = document.getElementById(`chart-${variable}`).getContext('2d');
    charts[variable] = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [
          {
            label: 'Real',
            data: [],
            borderColor: colors[variable],
            backgroundColor: colors[variable] + '20',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0
          },
          {
            label: 'Predicción IA',
            data: [],
            borderColor: '#ffffff',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            borderDash: [5, 5],
            hidden: true
          }
        ]
      },
      options: genericOptions
    });
  });

  setState({ charts });
  console.log('📊 Gráficas inicializadas');
}

export function updateGraphs() {
  const { data, charts, predictions, showPredictions } = getState();
  if (data.length === 0) return;

  variables.forEach(variable => {
    const chart = charts[variable];
    if (!chart) return;

    // Construir etiquetas (índices o timestamps)
    const labels = data.map((d, i) => d.index ?? i + 1);
    const realData = data.map(d => d[variable]);
    const lastValue = realData[realData.length - 1];

    chart.data.labels = labels;
    chart.data.datasets[0].data = realData;
    safeSetTextContent(variable+'-value', lastValue);
    
    if (predictions && predictions[variable]) {
      const predValues = predictions[variable];
      const predictionData = [...realData, ...predValues];
      const extendedLabels = [...labels];
      for (let i = 0; i < predValues.length; i++) {
        extendedLabels.push(labels.length + i);
      }
      chart.data.labels = extendedLabels;
      chart.data.datasets[1].data = predictionData;
      chart.data.datasets[1].hidden = !showPredictions;
    } else {
      chart.data.datasets[1].data = [];
      chart.data.datasets[1].hidden = true;
    }

    chart.update('none');
  });

  const { graphMode } = getState();
  if (graphMode === 'single') updateSingleGraph();
  if (graphMode === 'comparison') updateComparisonGraph();
}

export function updateSingleGraph() {
  const variable = document.getElementById('varSelect').value;
  const { data, predictions, showPredictions, singleChart } = getState();

  if (!singleChart) {
    const ctx = document.getElementById('singleCanvas').getContext('2d');
    const newChart = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [
          {
            label: 'Real',
            data: [],
            borderColor: colors[variable],
            borderWidth: 2,
            pointRadius: 0,
            tension: 0
          },
          {
            label: 'Predicción IA',
            data: [],
            borderColor: '#ffffff',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            borderDash: [5, 5],
            hidden: true
          }
        ]
      },
      options: genericOptions
    });
    setState({ singleChart: newChart });
  }

  const chart = getState().singleChart;
  const realData = data.map(d => d[variable]);
  const labels = data.map((d, i) => d.index ?? i + 1);

  chart.data.datasets[0].borderColor = colors[variable];
  chart.data.datasets[0].label = variable;
  chart.data.datasets[0].data = realData;
  chart.data.labels = labels;

  if (predictions && predictions[variable]) {
    const predValues = predictions[variable];
    const predictionData = [...realData, ...predValues];
    const extendedLabels = [...labels];
    for (let i = 0; i < predValues.length; i++) {
      extendedLabels.push(labels.length + i);
    }
    chart.data.labels = extendedLabels;
    chart.data.datasets[1].data = predictionData;
    chart.data.datasets[1].hidden = !showPredictions;
  } else {
    chart.data.datasets[1].data = [];
    chart.data.datasets[1].hidden = true;
  }

  chart.update('none');
}

export function updateComparisonGraph() {
  const { data, predictions, showPredictions, comparisonChart } = getState();

  if (!comparisonChart) {
    const ctx = document.getElementById('comparisonCanvas').getContext('2d');
    const newChart = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [
          { label: 'VoltajeEntrada (Real)', data: [], borderColor: colors.VoltajeEntrada, borderWidth: 2, pointRadius: 0, tension: 0 },
          { label: 'VoltajeSalida (Real)', data: [], borderColor: colors.VoltajeSalida, borderWidth: 2, pointRadius: 0, tension: 0 },
          { label: 'CorrienteEntrada (Real)', data: [], borderColor: colors.CorrienteEntrada, borderWidth: 2, pointRadius: 0, tension: 0 },
          { label: 'CorrienteSalida (Real)', data: [], borderColor: colors.CorrienteSalida, borderWidth: 2, pointRadius: 0, tension: 0 },
          { label: 'VoltajeEntrada (IA)', data: [], borderColor: '#ffffff', borderWidth: 2, pointRadius: 0, tension: 0.4, borderDash: [5, 5], hidden: true },
          { label: 'VoltajeSalida (IA)', data: [], borderColor: '#ffffff', borderWidth: 2, pointRadius: 0, tension: 0.4, borderDash: [5, 5], hidden: true },
          { label: 'CorrienteEntrada (IA)', data: [], borderColor: '#ffffff', borderWidth: 2, pointRadius: 0, tension: 0.4, borderDash: [5, 5], hidden: true },
          { label: 'CorrienteSalida (IA)', data: [], borderColor: '#ffffff', borderWidth: 2, pointRadius: 0, tension: 0.4, borderDash: [5, 5], hidden: true }
        ]
      },
      options: genericOptions
    });
    setState({ comparisonChart: newChart });
  }

  const chart = getState().comparisonChart;
  const labels = data.map((_, i) => i);
  const ve = data.map(d => d.VoltajeEntrada || 0);
  const vs = data.map(d => d.VoltajeSalida || 0);
  const ce = data.map(d => d.CorrienteEntrada || 0);
  const cs = data.map(d => d.CorrienteSalida || 0);

  chart.data.labels = labels;
  chart.data.datasets[0].data = ve;
  chart.data.datasets[1].data = vs;
  chart.data.datasets[2].data = ce;
  chart.data.datasets[3].data = cs;

  if (predictions) {
    const extendedLabels = [...labels];

    if (predictions.VoltajeEntrada) {
      const vePred = [...ve, ...predictions.VoltajeEntrada];
      chart.data.datasets[4].data = vePred;
      chart.data.datasets[4].hidden = !showPredictions;
    }
    if (predictions.VoltajeSalida) {
      const vsPred = [...vs, ...predictions.VoltajeSalida];
      chart.data.datasets[5].data = vsPred;
      chart.data.datasets[5].hidden = !showPredictions;
    }
    if (predictions.CorrienteEntrada) {
      const cePred = [...ce, ...predictions.CorrienteEntrada];
      chart.data.datasets[6].data = cePred;
      chart.data.datasets[6].hidden = !showPredictions;
    }
    if (predictions.CorrienteSalida) {
      const csPred = [...cs, ...predictions.CorrienteSalida];
      chart.data.datasets[7].data = csPred;
      chart.data.datasets[7].hidden = !showPredictions;
    }

    // Ajustar etiquetas si es necesario
    const maxPredLen = Math.max(
      predictions.VoltajeEntrada?.length || 0,
      predictions.VoltajeSalida?.length || 0,
      predictions.CorrienteEntrada?.length || 0,
      predictions.CorrienteSalida?.length || 0
    );
    for (let i = 0; i < maxPredLen; i++) {
      extendedLabels.push(labels.length + i);
    }
    chart.data.labels = extendedLabels;
  }

  chart.update('none');
}