// api.js - Funciones de comunicación con el backend

import { API_URL, WINDOW_SIZE } from './constants.js';
import { getState, setState } from './state.js';
import { updateGraphs, updateRealtimeDisplay, updateToggleRecordingStatus, safeSetTextContent, renderMeasurementsList, displayHistoricalWindow, updateSystemStatusDisplay } from './ui.js';

// Función principal de fetching (llamada periódica)
export async function fetchData() {
  try {
    const { isRecording, systemStatus } = getState();
    let changeStatus = false;
    const response = await fetch(`${API_URL}/esp32/status-measurement`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const json = await response.json();
    if (json.status !== 'ok') return;

    if (isRecording !== json.measuring) changeStatus = true;

    setState({ isRecording: json.measuring });
    if (changeStatus) updateToggleRecordingStatus();

    if (systemStatus.hybridEnabled && !isRecording) {
      await fetchHybridData();
    } else if (isRecording) {
      await fetchTraditionalData();
    }
  } catch (error) {
    console.error('Error en fetchData:', error);
    await fetchTraditionalData(); // fallback
  }
}

export async function fetchHybridData() {
  try {
    const { data: currentData, lastSampleId } = getState();
    const startIndex = currentData.length;
    const response = await fetch(`${API_URL}/data/stream?last_sample=${lastSampleId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const json = await response.json();
    if (json.error) {
      console.warn('⚠️ Error en respuesta streaming:', json.error);
      return;
    }

    if (json.measurements && json.measurements.length > 0) {
      const newLastSampleId = json.last_sample;
      setState({ lastSampleId: newLastSampleId });

      const now = new Date();
      const newData = json.measurements.map((m, i) => {
        const timestamp = m.timestamp ? new Date(m.timestamp).getTime() : now.getTime() - (json.measurements.length - i - 1) * 1000;
        return {
          //index: m.rowid,
          index: startIndex + i + 1,
          timestamp: timestamp,
          ...m
        };
      });

      // Mantener solo los últimos MAX_POINTS
      const { MAX_POINTS } = getState();
      newData.forEach(d => currentData.push(d));
      if (currentData.length > MAX_POINTS) {
        currentData.splice(0, currentData.length - MAX_POINTS);
      }
      setState({ data: currentData });

      const realtimeData = newData[newData.length - 1] || currentData[currentData.length - 1];
      setState({ realtimeData });

      updateGraphs();
      if (getState().activeTab === 'realtime') updateRealtimeDisplay();
      console.log(`📊 ${newData.length} nuevas muestras (última: ${lastSampleId})`);
    }
  } catch (error) {
    console.error('❌ Error en streaming híbrido:', error);
    throw error;
  }
}

export async function fetchTraditionalData() {
  try {
    const { MAX_POINTS } = getState();
    const response = await fetch(`${API_URL}/data?limit=${MAX_POINTS}`);
    if (!response.ok) return;

    const json = await response.json();
    if (json.measurements && json.measurements.length > 0) {
      const data = json.measurements.map((m, i) => ({
        //index: m.rowid || i,
        index: i + 1,
        ...m
      }));
      const realtimeData = json.measurements[json.measurements.length - 1];
      const lastSampleId = json.last_update || data[data.length - 1]?.rowid || 0;

      setState({ data, realtimeData, lastSampleId });

      updateGraphs();
      if (getState().activeTab === 'realtime') updateRealtimeDisplay();
    }
  } catch (error) {
    console.error('❌ Error en fetch tradicional:', error);
  }
}

export async function checkHybridSystemStatus() {
  try {
    const response = await fetch(`${API_URL}/system/status`);
    if (!response.ok) return;

    const json = await response.json();
    if (json.status === 'ok') {
      const systemStatus = {
        hybridEnabled: true,
        cacheSamples: json.hybrid_system?.sqlite_cache?.total_samples || 0,
        postgresSamples: json.hybrid_system?.postgresql?.total_samples || 0
      };
      setState({ systemStatus });

      console.log('✅ Sistema híbrido funcionando');
      console.log('💾 Cache SQLite:', systemStatus.cacheSamples, 'muestras');
      console.log('🗄️ PostgreSQL:', systemStatus.postgresSamples, 'muestras');

      updateSystemStatusDisplay();
    }
  } catch (error) {
    console.log('⚠️ Sistema híbrido no disponible, usando modo tradicional');
    setState({ systemStatus: { ...getState().systemStatus, hybridEnabled: false } });
  }
}

export async function loadMeasurementsList() {
  try {
    console.log('📋 Cargando lista de mediciones...');
    const container = document.getElementById('measurementsList');
    if (!container) return;

    container.innerHTML = `
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>Cargando lista de mediciones...</p>
      </div>
    `;

    let response, json;

    // Intento con resumen híbrido (comentado por ahora)
    // if (systemStatus.hybridEnabled) { ... }

    response = await fetch(`${API_URL}/measurements/list`);
    json = await response.json();

    if (json.status === 'ok' && json.measurements) {
      json.measurements.forEach(m => m.source = 'postgresql');
    }

    if (json.status === 'ok' && json.measurements && json.measurements.length > 0) {
      setState({ allMeasurements: json.measurements });
      renderMeasurementsList();
      console.log(`✅ ${json.measurements.length} mediciones cargadas`);
    } else {
      container.innerHTML = `
        <div class="no-measurements">
          <p>No hay mediciones guardadas aún</p>
          <p style="font-size: 12px; margin-top: 10px;">Inicia una grabación para crear mediciones</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('❌ Error cargando mediciones:', error);
    const container = document.getElementById('measurementsList');
    if (container) {
      container.innerHTML = `
        <div class="no-measurements">
          <p>Error al cargar mediciones</p>
          <p style="font-size: 12px; margin-top: 10px;">${error.message}</p>
        </div>
      `;
    }
  }
}

export async function loadSelectedMeasurementData() {
  const { selectedMeasurementId, selectedMeasurementNumSamples } = getState();
  if (!selectedMeasurementId) {
    alert('Por favor, selecciona una medición primero');
    return;
  }

  try {
    console.log(`📊 Cargando datos de medición #${selectedMeasurementId}...`);

    const container = document.getElementById('camViewGrid');
    container.innerHTML = `
      <div class="loading-spinner" style="grid-column: 1 / -1;">
        <div class="spinner"></div>
        <p>Cargando datos de la medición...</p>
      </div>
    `;

    const response = await fetch(
      `${API_URL}/data/measurement/${selectedMeasurementId}?page=1&page_size=${selectedMeasurementNumSamples}&use_cache=true`
    );
    const json = await response.json();

    if (json.status === 'ok') {
      const selectedMeasurementData = json.measurements || [];
      setState({ selectedMeasurementData });

      const timelineControls = document.getElementById('timelineControls');
      if (timelineControls) timelineControls.style.display = 'block';

      const slider = document.getElementById('timelineSlider');
      const maxPosition = Math.max(0, selectedMeasurementData.length - WINDOW_SIZE);

      slider.max = maxPosition;
      slider.disabled = selectedMeasurementData.length === 0;
      slider.value = maxPosition;

      safeSetTextContent('timelineTotal', selectedMeasurementData.length);
      safeSetTextContent('windowSize', Math.min(WINDOW_SIZE, selectedMeasurementData.length));

      // Limpiar gráficas anteriores
      setState({ camCharts: {} });

      const currentSliderPosition = maxPosition;
      setState({ currentSliderPosition });
      displayHistoricalWindow(currentSliderPosition);

      console.log(`✅ ${selectedMeasurementData.length} muestras cargadas`);
    } else {
      throw new Error(json.message || 'Error al cargar datos');
    }
  } catch (error) {
    console.error('❌ Error cargando datos de medición:', error);
    const container = document.getElementById('camViewGrid');
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">⚠️</div>
        <h3>Error al cargar datos</h3>
        <p>${error.message}</p>
      </div>
    `;
  }
}

export async function toggleRecording() {
  const { isRecording } = getState();
  const newIsRecording = !isRecording;
  setState({ isRecording: newIsRecording });
  updateToggleRecordingStatus();

  try {
    let response;
    if (newIsRecording) {
      response = await fetch(`${API_URL}/esp32/start-measurement`, { method: 'POST' });
    } else {
      response = await fetch(`${API_URL}/esp32/end-measurement`, { method: 'POST' });
    }

    if (!response.ok) {
      newIsRecording = !newIsRecording;
      setState({ isRecording: newIsRecording });
      updateToggleRecordingStatus();
      return;
    }

    const json = await response.json();
    if (json.status === 'ok') {
      console.log('✅ Sistema de medición funcionando');
    }
  } catch (error) {
    console.log('⚠️ Sistema de medición no disponible');
    updateToggleRecordingStatus();
  }
}

export async function clearAllHistory() {
  const { selectedMeasurementId } = getState();
  if (!selectedMeasurementId) {
    alert('Por favor, selecciona una medición primero');
    return;
  }

  if (!confirm('¿Estás seguro de que quieres eliminar la medición: ' + selectedMeasurementId + ' de las grabaciones?\nEsta acción no se puede deshacer.')) {
    return;
  }

  console.log('🗑️ Solicitando eliminación de ' + selectedMeasurementId + ' de las grabaciones...');

  try {
    const deleteResponse = await fetch(`${API_URL}/measurements/${selectedMeasurementId}`, {
      method: 'DELETE'
    });
    const deleteResult = await deleteResponse.json();

    if (deleteResult.status === 'ok') {
      alert('Medición eliminada');
    }
  } catch (error) {
    alert('Error al eliminar la medición');
    console.error(`Error eliminando medición ${selectedMeasurementId}:`, error);
    return;
  }

  // Limpiar datos locales
  setState({
    selectedMeasurementId: null,
    selectedMeasurementData: [],
    allMeasurements: [],
    camCharts: {}
  });

  // Ocultar controles y gráficas
  const details = document.getElementById('measurementDetails');
  if (details) details.style.display = 'none';

  const timelineControls = document.getElementById('timelineControls');
  if (timelineControls) timelineControls.style.display = 'none';

  const container = document.getElementById('camViewGrid');
  if (container) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">📊</div>
        <h3>Selecciona una medición</h3>
        <p>Selecciona una medición de la lista para ver sus datos</p>
      </div>
    `;
  }

  // Recargar lista
  loadMeasurementsList();
}