#backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path

app = FastAPI()

# Para permitir acceso desde navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de datos recibido
class Measurement(BaseModel):
    VoltajeEntrada: float
    VoltajeDiodo: float
    VoltajeSalida: float
    CorrienteEntrada: float
    CorrienteInductor: float
    CorrienteDiodo: float
    CorrienteSalida: float

# Lista en memoria para prueba
data_storage = []

DATA_FILE = Path("mediciones.json")

# Crear archivo si no existe
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def save_to_json(data: dict):
    # Cargar los datos actuales
    with open(DATA_FILE, "r") as f:
        current_data = json.load(f)

    # Agregar el nuevo dato
    current_data.append(data)

    # Guardar de nuevo
    with open(DATA_FILE, "w") as f:
        json.dump(current_data, f, indent=4)

#Metodos GET
@app.get("/")
def root():
    return {"msg": "Servidor listo"}

@app.get("/data")
def get_data():
    return {"measurements": data_storage[-20:]}  # últimos 20 datos

#Metodos POST
@app.post("/esp32/data")
def receive_data(payload: Measurement):
    data_dict = payload.dict()
    data_storage.append(data_dict)
    save_to_json(data_dict)
    return {"status": "ok", "data": payload}

