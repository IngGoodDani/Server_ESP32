// utils.js - Funciones de utilidad general

import { variables } from './constants.js';
import { getState } from './state.js';

export function saveToCSV() {
  const { data } = getState();
  if (data.length === 0) {
    alert('No hay datos para guardar');
    return;
  }

  const headers = ['Index', ...variables, 'Fecha', 'Hora'].join(',');
  const rows = data.map(row => {
    const fullTimestamp = row.marcaTiempo || row.timestamp;
    let dateOnly = '';
    let timeOnly = '';

    if (fullTimestamp) {
      const parts = fullTimestamp.split(' ');
      timeOnly = parts[1];
      dateOnly = parts[0];
    }

    return [
      row.index || row.rowid,
      ...variables.map(v => row[v] || 'N/A'),
      dateOnly,
      timeOnly
    ].join(',');
  });

  const csv = [headers, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mediciones_${new Date().toISOString()}.csv`;
  a.click();
  URL.revokeObjectURL(url);

  console.log(`💾 CSV guardado: ${data.length} muestras`);
}

export function saveToCSVSingle() {
  const { data } = getState();
  if (data.length === 0) {
    alert('No hay datos para guardar');
    return;
  }

  const variable = document.getElementById('varSelect').value;

  const headers = ['Index', variable, 'Fecha', 'Hora'].join(',');
  const rows = data.map(row => {
    const fullTimestamp = row.marcaTiempo || row.timestamp;
    let dateOnly = '';
    let timeOnly = '';

    if (fullTimestamp) {
      const parts = fullTimestamp.split(' ');
      timeOnly = parts[1];
      dateOnly = parts[0];
    }

    return [
      row.index || row.rowid,
      row[variable] || 'N/A',
      dateOnly,
      timeOnly
    ].join(',');
  });

  const csv = [headers, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mediciones_${variable}_${new Date().toISOString()}.csv`;
  a.click();
  URL.revokeObjectURL(url);

  console.log(`💾 CSV guardado: ${data.length} muestras`);
}