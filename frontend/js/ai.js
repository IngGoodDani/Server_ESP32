// ai.js - Funciones relacionadas con predicciones de IA

import { API_URL } from './constants.js';
import { getState, setState } from './state.js';
import { updateGraphs, safeSetTextContent } from './ui.js';

export function updatePredictionHorizon(event) {
  const horizon = parseInt(event.target.value);
  setState({ predictionHorizon: horizon });
  safeSetTextContent('horizonValue', horizon);
  console.log(`Horizonte de predicción actualizado: ${horizon} pasos`);
}

export async function fetchPredictions() {
  const { isPredicting, predictionHorizon } = getState();
  if (isPredicting) {
    console.log('⏳ Ya hay una predicción en proceso...');
    return;
  }

  try {
    setState({ isPredicting: true });
    console.log(`🧠 Solicitando predicciones con horizonte de ${predictionHorizon} pasos...`);

    const btn = document.getElementById('btnPredict');
    btn.disabled = true;
    btn.textContent = '⏳ Procesando...';

    safeSetTextContent('predictionStatus', '🔄 Generando predicciones...');
    document.getElementById('predictionStatus').style.display = 'block';

    const response = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ horizon: predictionHorizon })
    });

    const json = await response.json();

    if (json.status === 'ok' && json.prediction) {
      setState({
        predictions: json.prediction,
        showPredictions: true
      });

      document.getElementById('btnTogglePred').disabled = false;
      document.getElementById('btnTogglePred').classList.add('active');

      if (json.metrics) {
        safeSetTextContent('aiRMSE', json.metrics.rmse ? json.metrics.rmse.toFixed(4) : '--');
      }

      safeSetTextContent('predictionStatus', `✅ ${predictionHorizon} predicciones generadas exitosamente`);

      alert(
        '✅ Predicciones generadas exitosamente\n\n' +
        `📊 Muestras usadas: ${json.samples_used}\n` +
        `📈 Horizonte: ${predictionHorizon} pasos futuros\n` +
        `🎯 RMSE: ${json.metrics?.rmse?.toFixed(4) || '--'}`
      );

      console.log('✅ Predicciones generadas:', json);
      updateGraphs();
    } else {
      throw new Error(json.detail || 'Error desconocido');
    }
  } catch (error) {
    console.error('❌ Error en predicción:', error);
    safeSetTextContent('predictionStatus', `❌ Error: ${error.message}`);
    alert(`❌ Error al obtener predicciones:\n\n${error.message}\n\nAsegúrate de tener al menos 120 muestras guardadas en la base de datos.`);
  } finally {
    setState({ isPredicting: false });
    const btn = document.getElementById('btnPredict');
    btn.disabled = false;
    btn.textContent = '🧠 Predicción IA';

    setTimeout(() => {
      const status = document.getElementById('predictionStatus');
      if (status) status.style.display = 'none';
    }, 3000);
  }
}

export function togglePredictions() {
  const { showPredictions } = getState();
  const newShow = !showPredictions;
  setState({ showPredictions: newShow });

  const btn = document.getElementById('btnTogglePred');
  btn.textContent = newShow ? 'Ocultar Predicciones' : 'Mostrar Predicciones';
  btn.classList.toggle('active', newShow);

  updateGraphs();
  console.log(newShow ? '👁️ Predicciones mostradas' : '🙈 Predicciones ocultas');
}