# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

#Metodos GET
@app.get("/")
def root():
    return {"msg": "Servidor de prueba ESP32 listo"}

@app.get("/data")
def get_data():
    return {"measurements": data_storage[-10:]}  # últimos 10 datos

#Metodos POST
@app.post("/esp32/data")
def receive_data(payload: Measurement):
    data_storage.append(payload.dict())
    return {"status": "ok", "data": payload}
