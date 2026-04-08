let realTime = true;
let fetchInterval;
const charts = {};
let allMeasurements = []; // guarda todas las mediciones históricas

document.addEventListener("DOMContentLoaded", () => {
	const toggle = document.getElementById("toggleMode");
	const slider = document.getElementById("timeSlider");
	const label = document.getElementById("sliderLabel");
	
	// Iniciar en tiempo real
	startRealTime();
	
	toggle.addEventListener("change", () => {
		realTime = !toggle.checked;
		if (realTime) {
			label.textContent = "Tiempo actual";
			startRealTime();
		} else {
			stopRealTime();
			loadHistoricalData();
		}
	});
	
	slider.addEventListener("input", () => {
		if (!realTime) {
			const index = parseInt(slider.value);
			updateChartsWithHistory(index);
			label.textContent = `Tiempo: ${index}`;
		}
	});
});

function startRealTime() {
	fetchInterval = setInterval(fetchData, 500);
}

function stopRealTime() {
	clearInterval(fetchInterval);
}

async function fetchData() {
	const res = await fetch("http://localhost:8000/data");
	const json = await res.json();
	const measurements = json.measurements;
	if (measurements.length === 0) return;
	
	allMeasurements.push(...measurements); // guardamos los datos
	updateTable(measurements);
	
	const last = measurements[measurements.length - 1];
	const now = new Date().toLocaleTimeString();
	
	const variables = {
		"VoltajeEntrada": last.VoltajeEntrada,
		"VoltajeDiodo": last.VoltajeDiodo,
		"VoltajeSalida": last.VoltajeSalida,
		"CorrienteEntrada": last.CorrienteEntrada,
		"CorrienteInductor": last.CorrienteInductor,
		"CorrienteDiodo": last.CorrienteDiodo,
		"CorrienteSalida": last.CorrienteSalida
	};
	
	for (const [key, value] of Object.entries(variables)) {
		if (!charts[key]) {
			charts[key] = new Chart(document.getElementById(key), {
				type: "line",
				data: {
					labels: [now],
					datasets: [{ label: key, data: [value], borderColor: getRandomColor(), fill: false }]
				},
				options: {
					animation: false,
					scales: { x: { display: true }, y: { beginAtZero: true } }
				}
			});
		} else {
			const chart = charts[key];
			chart.data.labels.push(now);
			chart.data.datasets[0].data.push(value);
		
			if (chart.data.labels.length > 100) {
				chart.data.labels.shift();
				chart.data.datasets[0].data.shift();
			}
			chart.update();
		}
	}
}

async function loadHistoricalData() {
	// Simula lectura del historial desde el servidor
	const res = await fetch("http://localhost:8000/history");
	const json = await res.json();
	allMeasurements = json.measurements;
	
	const slider = document.getElementById("timeSlider");
	slider.max = allMeasurements.length - 1;
	updateChartsWithHistory(slider.value);
}

function updateChartsWithHistory(index) {
	const data = allMeasurements.slice(0, index);
	
	const labels = data.map((_, i) => i);
	const variables = Object.keys(charts);
	
	for (const key of variables) {
		const chart = charts[key];
		chart.data.labels = labels;
		chart.data.datasets[0].data = data.map(d => d[key]);
		chart.update();
	}
}

function updateTable(measurements) {
	const table = document.getElementById("data-table");
	table.innerHTML = "<tr><th>VoltajeEntrada</th><th>VoltajeDiodo</th><th>VoltajeSalida</th><th>CorrienteEntrada</th><th>CorrienteInductor</th><th>CorrienteDiodo</th><th>CorrienteSalida</th></tr>";
	measurements.forEach(row => {
		table.innerHTML += `<tr>
		<td>${row.VoltajeEntrada}</td>
		<td>${row.VoltajeDiodo}</td>
		<td>${row.VoltajeSalida}</td>
		<td>${row.CorrienteEntrada}</td>
		<td>${row.CorrienteInductor}</td>
		<td>${row.CorrienteDiodo}</td>
		<td>${row.CorrienteSalida}</td>
		</tr>`;
	});
}

