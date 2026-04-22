// ui.js - Manejo de la interfaz de usuario (eventos, actualizaciones DOM)

import { variables, colors, WINDOW_SIZE, scales } from './constants.js';
import { getState, setState } from './state.js';
import { toggleRecording, loadMeasurementsList, clearAllHistory, loadSelectedMeasurementData } from './api.js';
import { updateSingleGraph, updateComparisonGraph, updateGraphs } from './graphs.js';
import { displayHistoricalWindow } from './history.js';
import { togglePredictions, updatePredictionHorizon, fetchPredictions } from './ai.js';
import { saveToCSV, saveToCSVSingle } from './utils.js';

// Re-exportar funciones que otros módulos necesitan
export { safeSetTextContent, updateRealtimeDisplay, updateToggleRecordingStatus, renderMeasurementsList, selectMeasurement, updateSystemStatusDisplay, onTimelineChange, togglePlayback, jumpToStart, jumpToEnd, stepBack, stepForward, updateGraphs, displayHistoricalWindow, formatTimestamp, calculateDuration, retryLoadMeasurement, updateCamTimestamp, switchTab, switchGraphMode };

// Inicializar event listeners (llamado desde main)
export function initEventListeners() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => switchGraphMode(btn.dataset.mode));
  });

  document.getElementById('btnRecord').addEventListener('click', toggleRecording);
  document.getElementById('btnCSV').addEventListener('click', saveToCSV);
  document.getElementById('btnCSVSingle').addEventListener('click', saveToCSVSingle);
  document.getElementById('btnPredict').addEventListener('click', fetchPredictions);
  document.getElementById('btnTogglePred').addEventListener('click', togglePredictions);
  document.getElementById('btnSetSampling').addEventListener('click', updateMeasureTime);
  
  document.getElementById('varSelect').addEventListener('change', updateSingleGraph);
  document.getElementById('timeUnit').addEventListener('change', updateUnit);
  document.getElementById('samplingTime').addEventListener('input', updateSamplingTime);
  document.getElementById('sampScaleTime').addEventListener('input', updateSampScaleTime);

  // Eventos del historial
  document.getElementById('btnRefreshMeasurements').addEventListener('click', loadMeasurementsList);
  document.getElementById('btnClearHistory').addEventListener('click', clearAllHistory);
  document.getElementById('btnLoadMeasurementData').addEventListener('click', loadSelectedMeasurementData);

  // Eventos del timeline
  document.getElementById('timelineSlider').addEventListener('input', onTimelineChange);
  document.getElementById('btnPlayback').addEventListener('click', togglePlayback);
  document.getElementById('btnJumpStart').addEventListener('click', jumpToStart);
  document.getElementById('btnJumpEnd').addEventListener('click', jumpToEnd);
  document.getElementById('btnStepBack').addEventListener('click', stepBack);
  document.getElementById('btnStepForward').addEventListener('click', stepForward);

  // Eventos de predicción IA
  document.getElementById('predictionHorizon').addEventListener('input', updatePredictionHorizon);
}

function switchTab(tabName) {
  setState({ activeTab: tabName });

  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  document.getElementById(`tab-${tabName}`).classList.add('active');

  if (tabName === 'realtime') updateRealtimeDisplay();
  if (tabName === 'history') {
    loadMeasurementsList();
  }

  // Pausar streaming si no estamos en tiempo real o gráficas
  if (tabName !== 'graphs' && tabName !== 'realtime') {
    pauseStreaming();
  } else {
    resumeStreaming();
  }
}

function switchGraphMode(mode) {
  setState({ graphMode: mode });

  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`[data-mode="${mode}"]`).classList.add('active');

  document.getElementById('allGraphs').classList.toggle('hidden', mode !== 'all');
  document.getElementById('singleGraph').classList.toggle('hidden', mode !== 'single');
  document.getElementById('comparisonGraph').classList.toggle('hidden', mode !== 'comparison');

  if (mode === 'single') updateSingleGraph();
  if (mode === 'comparison') updateComparisonGraph();
}

function updateToggleRecordingStatus() {
  const btn = document.getElementById('btnRecord');
  const { isRecording } = getState();
  btn.textContent = isRecording ? '⏸ Pausar' : '▶ Iniciar';
  btn.classList.toggle('recording', isRecording);

  console.log(isRecording ? '▶️ Grabación iniciada' : '⏸️ Grabación pausada');
}

function updateRealtimeDisplay() {
  const { realtimeData } = getState();
  if (!realtimeData) {
    console.log('ℹ️ No hay datos en tiempo real disponibles');
    return;
  }

  const container = document.getElementById('realtimeGrid');
  container.innerHTML = '';

  const timestampDisplay = document.getElementById('realtimeTimestamp');
  if (timestampDisplay) {
    timestampDisplay.textContent = realtimeData.timestamp ?
      formatTimestamp(realtimeData.timestamp) :
      new Date().toLocaleTimeString();
  }

  variables.forEach(variable => {
    const card = document.createElement('div');
    card.className = 'realtime-card';
    card.style.background = `linear-gradient(135deg, ${colors[variable]} 0%, ${colors[variable]}cc 100%)`;

    const value = realtimeData[variable];
    const displayValue = value !== null && value !== undefined ? value.toFixed(3) : 'N/A';

    card.innerHTML = `
      <div class="label">${variable}</div>
      <div class="value">${displayValue}</div>
      <div class="unit">${variable.includes('Corriente') ? 'Amperios' : variable.includes('Voltaje') ? 'Voltios' : 'Wats'}</div>
    `;
    container.appendChild(card);
  });
}

function updateCamTimestamp() {
  const now = new Date();
  const timestamp = now.toTimeString().split(' ')[0];
  safeSetTextContent('camTimestamp', timestamp);
}

function safeSetTextContent(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = value;
  } else {
    console.warn(`Elemento no encontrado: ${elementId}`);
  }
}

function renderMeasurementsList() {
  const container = document.getElementById('measurementsList');
  if (!container) return;

  const { allMeasurements, selectedMeasurementId } = getState();

  if (allMeasurements.length === 0) {
    container.innerHTML = `
      <div class="no-measurements">
        <p>No hay mediciones guardadas aún</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';

  allMeasurements.forEach(measurement => {
    const measurementItem = document.createElement('div');
    measurementItem.className = 'measurement-item';
    if (selectedMeasurementId === measurement.id) {
      measurementItem.classList.add('selected');
    }

    measurementItem.dataset.id = measurement.id;

    const fecha = measurement.fecha || 'N/A';
    const horaInicio = measurement.hora_inicio ? measurement.hora_inicio.substring(0, 8) : 'N/A';
    const horaTermino = measurement.hora_termino ? measurement.hora_termino.substring(0, 8) : 'N/A';
    const sourceIcon = measurement.source === 'cache_sqlite' ? '💾' : '🗄️';

    measurementItem.innerHTML = `
      <div class="measurement-info">
        <div class="measurement-id">${sourceIcon} Medición #${measurement.id}</div>
        <div class="measurement-date">${fecha}</div>
      </div>
      <div class="measurement-time">
        <span>Inicio: ${horaInicio}</span>
        <span>Fin: ${horaTermino}</span>
      </div>
      <div class="measurement-stats">
        <div class="stat-item">
          <div class="stat-label">Muestras</div>
          <div class="stat-value">${measurement.num_samples || 0}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Duración</div>
          <div class="stat-value">${calculateDuration(measurement.hora_inicio, measurement.hora_termino)}</div>
        </div>
      </div>
    `;

    measurementItem.addEventListener('click', () => {
      selectMeasurement(measurement.id, measurement.num_samples);
    });

    container.appendChild(measurementItem);
  });
}

function selectMeasurement(measurementId, measurementSamples) {
  document.querySelectorAll('.measurement-item').forEach(item => {
    item.classList.remove('selected');
  });

  const selectedItem = document.querySelector(`.measurement-item[data-id="${measurementId}"]`);
  if (selectedItem) {
    selectedItem.classList.add('selected');
  }

  setState({
    selectedMeasurementId: measurementId,
    selectedMeasurementNumSamples: measurementSamples,
    currentPage: 1
  });

  const measurement = getState().allMeasurements.find(m => m.id === measurementId);
  if (measurement) {
    const details = document.getElementById('measurementDetails');
    if (details) details.style.display = 'block';

    const infoContainer = document.getElementById('measurementInfo');
    if (infoContainer) {
      infoContainer.innerHTML = `
        <div class="info-item">
          <div class="info-label">ID</div>
          <div class="info-value">#${measurement.id}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Fecha</div>
          <div class="info-value">${measurement.fecha || 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Hora Inicio</div>
          <div class="info-value">${measurement.hora_inicio ? measurement.hora_inicio.substring(0, 8) : 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Hora Fin</div>
          <div class="info-value">${measurement.hora_termino ? measurement.hora_termino.substring(0, 8) : 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Duración</div>
          <div class="info-value">${calculateDuration(measurement.hora_inicio, measurement.hora_termino)}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Muestras</div>
          <div class="info-value">${measurement.num_samples || 0}</div>
        </div>
      `;
    }

    safeSetTextContent('currentMeasurementId', measurement.id);
  }
}

function calculateDuration(startTime, endTime) {
  if (!startTime || !endTime) return 'N/A';

  try {
    const start = new Date(`1970-01-01T${startTime}`);
    const end = new Date(`1970-01-01T${endTime}`);

    const diffMs = end - start;
    const diffSec = Math.floor(diffMs / 1000);
    const minutes = Math.floor(diffSec / 60);
    const seconds = diffSec % 60;

    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  } catch (error) {
    return 'N/A';
  }
}

function formatTimestamp(timestamp) {
  if (!timestamp) return '';

  try {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  } catch (error) {
    return timestamp.toString();
  }
}

function retryLoadMeasurement() {
  const { selectedMeasurementId } = getState();
  if (selectedMeasurementId) {
    loadSelectedMeasurementData();
  }
}

function onTimelineChange(event) {
  const position = parseInt(event.target.value);
  stopPlayback();
  displayHistoricalWindow(position);
}

function togglePlayback() {
  const { playbackInterval } = getState();
  if (playbackInterval) {
    stopPlayback();
  } else {
    startPlayback();
  }
}

function startPlayback() {
  const btn = document.getElementById('btnPlayback');
  btn.textContent = '⏸️ Pausar';

  const interval = setInterval(() => {
    const { selectedMeasurementData, currentSliderPosition } = getState();
    const maxPosition = Math.max(0, selectedMeasurementData.length - WINDOW_SIZE);

    let newPosition;
    if (currentSliderPosition >= maxPosition) {
      newPosition = 0;
    } else {
      newPosition = Math.min(currentSliderPosition + 10, maxPosition);
    }

    setState({ currentSliderPosition: newPosition });
    displayHistoricalWindow(newPosition);
  }, 100);

  setState({ playbackInterval: interval });
}

function stopPlayback() {
  const { playbackInterval } = getState();
  if (playbackInterval) {
    clearInterval(playbackInterval);
    setState({ playbackInterval: null });

    const btn = document.getElementById('btnPlayback');
    btn.textContent = '▶️ Reproducir';
  }
}

function jumpToStart() {
  stopPlayback();
  displayHistoricalWindow(0);
}

function jumpToEnd() {
  stopPlayback();
  const { selectedMeasurementData } = getState();
  const maxPosition = Math.max(0, selectedMeasurementData.length - WINDOW_SIZE);
  displayHistoricalWindow(maxPosition);
}

function stepBack() {
  const stepSize = 10;
  const { currentSliderPosition } = getState();
  const newPosition = Math.max(0, currentSliderPosition - stepSize);
  stopPlayback();
  displayHistoricalWindow(newPosition);
}

function stepForward() {
  const stepSize = 10;
  const { selectedMeasurementData, currentSliderPosition } = getState();
  const maxPosition = Math.max(0, selectedMeasurementData.length - WINDOW_SIZE);
  const newPosition = Math.min(maxPosition, currentSliderPosition + stepSize);
  stopPlayback();
  displayHistoricalWindow(newPosition);
}

function updateSystemStatusDisplay() {
  const statusElement = document.getElementById('systemStatus');
  if (!statusElement) return;

  const { systemStatus } = getState();
  statusElement.innerHTML = `
    <div style="font-size: 11px; color: #9ca3af; padding: 4px 8px; background: #1f2937; border-radius: 4px; margin: 5px 0; display: flex; justify-content: space-between;">
      <span>⚡ Sistema Híbrido</span>
      <span>💾 Cache: ${systemStatus.cacheSamples} | 🗄️ PG: ${systemStatus.postgresSamples}</span>
    </div>
  `;
}

function updateSamplingTime(event) {
    const horizon = parseInt(event.target.value, 10);
    const timeUnit = document.getElementById('timeUnit');
    setState({ samplingTime: horizon });
    safeSetTextContent('timeValue', horizon);
    safeSetTextContent('timeLabel', timeUnit.value);
    //console.log(`Tiempo de muestreo actualizado: ${horizon} `);
}

function updateUnit() {
    const timeUnit = document.getElementById('timeUnit');
    const samplingTime = document.getElementById('samplingTime');
    const config = scales[timeUnit.value];
    samplingTime.min = config.min;
    samplingTime.max = config.max;
    samplingTime.step = config.step;

    if (+samplingTime.value < config.min) samplingTime.value = config.min;
    if (+samplingTime.value > config.max) samplingTime.value = config.max;

    safeSetTextContent('timeLabel', timeUnit.value);
    safeSetTextContent('timeValue', samplingTime.value);
    setState({ timeUnit: timeUnit.value });
}
  
function updateSampScaleTime(event) {
  const horizon = parseInt(event.target.value);
  setState({ MAX_POINTS: horizon });
  safeSetTextContent('scaleTime', horizon);
  //console.log(`Escala de tiempo actualizada: ${horizon} `);
}

function pauseStreaming() {
  const { isStreaming } = getState();
  if (!isStreaming) return;
  setState({ isStreaming: false });
}

function resumeStreaming() {
  const { isStreaming } = getState();
  if (isStreaming) return;
  setState({ isStreaming: true });
}

function updateMeasureTime() {
    const timeUnit = document.getElementById('timeUnit');
    const samplingTime = document.getElementById('samplingTime');
    console.log(`Escala de tiempo actualizada: ${samplingTime.value} ${timeUnit.value} `);
}