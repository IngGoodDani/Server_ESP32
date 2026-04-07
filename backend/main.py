#backend/main.py
import threading
import webbrowser
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
from pathlib import Path
import uvicorn

from datetime import datetime

current_medicion = None  # Aquí se guarda la medición activa

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
FRONT_DIR = BASE_DIR.parent / "frontend"
INDEX_FILE = FRONT_DIR / "index.html"

app.mount("/js", StaticFiles(directory=FRONT_DIR / "js"), name="js")
app.mount("/css", StaticFiles(directory=FRONT_DIR / "css"), name="css")

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
    global current_medicion
    if current_medicion is None:
        return {"error": "No hay medición activa"}

    data_dict = payload.dict()
    current_medicion["datos"].append(data_dict)
    return {"status": "ok", "data": payload}

@app.post("/medicion/iniciar")
def iniciar_medicion():
    global current_medicion
    current_medicion = {
        "fecha_inicio": datetime.now().isoformat(),
        "fecha_fin": None,
        "datos": []
    }
    return {"status": "medicion iniciada"}

@app.post("/medicion/finalizar")
def finalizar_medicion():
    global current_medicion
    if current_medicion is None:
        return {"error": "No hay medición activa"}

    current_medicion["fecha_fin"] = datetime.now().isoformat()

    # Guardar en JSON
    with open(DATA_FILE, "r") as f:
        mediciones = json.load(f)
    mediciones.append(current_medicion)
    with open(DATA_FILE, "w") as f:
        json.dump(mediciones, f, indent=4)

    # Guardar en base de datos
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        database="mediciones",
        user="usuario_rw",
        password="convertidores"
    )
    cur = conn.cursor()

    # Insertar medición principal y obtener ID
    cur.execute("""
        INSERT INTO MEDICIONES (Fecha, Hora_Inicio, Hora_Termino)
        VALUES (%s, %s, %s)
        RETURNING ID_Mediciones;
    """, (
        current_medicion["fecha_inicio"][:10],  # fecha en formato YYYY-MM-DD
        current_medicion["fecha_inicio"][11:19],  # hora en formato HH:MM:SS
        current_medicion["fecha_fin"][11:19]
    ))
    id_medicion = cur.fetchone()[0]

    # Insertar cada dato de la sesión
    for m in current_medicion["datos"]:
        cur.execute("""
            INSERT INTO VOLTAJES (ID_Mediciones, Entrada, Diodo, Salida)
            VALUES (%s, %s, %s, %s);
        """, (id_medicion, m["VoltajeEntrada"], m["VoltajeDiodo"], m["VoltajeSalida"]))
        cur.execute("""
            INSERT INTO CORRIENTES (ID_Mediciones, Entrada, Diodo, Inductor, Salida)
            VALUES (%s, %s, %s, %s, %s);
        """, (
            id_medicion,
            m["CorrienteEntrada"],
            m["CorrienteDiodo"],
            m["CorrienteInductor"],
            m["CorrienteSalida"]
        ))

    conn.commit()
    cur.close()
    conn.close()

    current_medicion = None
    return {"status": "medición guardada y enviada a base de datos"}

@app.get("/", response_class=RedirectResponse)
def home_page():
    """Redirige a la aplicación principal"""
    return RedirectResponse(url="/app")

@app.get("/app", response_class=HTMLResponse)
def serve_app():
    """Sirve la interfaz principal HTML"""
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return HTMLResponse(content="<h1>Error: index.html no encontrado</h1>", status_code=404)
#    if os.path.exists("index.html"):
#        with open("index.html", "r", encoding="utf-8") as f:
#            return HTMLResponse(content=f.read())
#    
#    return HTMLResponse(content="<h1>Error: index.html no encontrado</h1>")

def init_system():
    """Inicializa el sistema"""
    print("=" * 60)
    print("\033[32m Iniciando sistema... \033[0m")
    print("=" * 60)

def open_browser():
    """Abre automáticamente el navegador"""
    url = "http://localhost:8000"
    print(f"\nAbriendo navegador en: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    init_system()
    
    threading.Timer(2.0, open_browser).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

#agregar modos de descarga, seleccionar datos para visualizar individualmente en el historico, poder visualizar las fechas y hora de las mediciones para poder seleccionar cual historico revizar, que muestre por dia, mes, por año para poder ver los identificadores y descargar los datos en una hoja de datos con los parametros seleccionados, conservar la tabla para poder ver los datos en ese momento aparte de las graficas en una interfaz distinta 
#Poner el boton de inicio para empezar a guardar los datos o despues del guardado poner una opcion para poder ver que datos se guardan
