#backend/main.py
import  threading
import  webbrowser
import  uvicorn
import  json
from    pathlib     import Path
from    fastapi     import FastAPI, WebSocket
from    pathlib     import Path
from    datetime    import datetime
from    fastapi.middleware.cors import  CORSMiddleware
from    fastapi.responses   import  RedirectResponse, HTMLResponse, FileResponse
from    fastapi.staticfiles import  StaticFiles
from    controllers.websocket_controller    import  WebSocketController
from    controllers.controller  import  Controller
from    DB.CL_DATABASE  import  HybridDatabase, AuxiliaresPG
from    models.measurement  import  Measurement


current_medicion = None  # Aquí se guarda la medición activa

app = FastAPI(title="Dashboard de Telemetría")

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

# Creación de objetos
db = HybridDatabase()
ws_controller = WebSocketController(db)
controll = Controller(db)

# Inicializar DB
db.init_sqlite()
db.init_postgres()

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

#----------------------------------------------------------
# Metodos GET
#----------------------------------------------------------
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

@app.get("/data")
def get_data():
    return {"measurements": data_storage[-20:]}  # últimos 20 datos

@app.get("/esp32/status-measurement")
def status_measurement():
    try:
        if db.current_measurement_id is None:
            return {
                "status": "ok", "measuring": False
            }
        else:
            return {
                "status": "ok", "measuring": True
            }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

#----------------------------------------------------------
# Metodos POST
#----------------------------------------------------------
@app.post("/esp32/data")
def receive_data(data: Measurement):
    """Recibe datos de la ESP32 por POST"""
    try:
        return controll.esp32_data(data)
    except Exception as e:
        return {"status": "error", "message": str(e)}

#----------------------------------------------------------
# Metodos PUT
#----------------------------------------------------------
@app.put("/esp32/start-measurement")
def start_measurement():
    """Inicia una nueva medición"""
    try:
        return controll.start_measurement()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.put("/esp32/end-measurement")
def end_measurement():
    """Finaliza la medición actual"""
    try:
        return controll.end_measurement()
    except Exception as e:
        return {"status": "error", "message": str(e)}

#----------------------------------------------------------
# Metodos DELETE
#----------------------------------------------------------
@app.delete("/cache/cleanup")
def cleanup_cache(days_to_keep: int = 7):
    """Limpia datos antiguos"""
    try:
        deleted = db.cleanup_old_data(days_to_keep)
        return {"status": "ok", "deleted_count": deleted}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/cache/cleanup/all")
def cleanup_all_cache():
    """Limpia todos los datos antiguos"""
    try:
        deleted = db.cleanup_all_data()
        return {"status": "ok", "deleted_count": deleted}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/measurements/{measurement_id}")
def delete_measurement_sample(measurement_id: int):
    """Elimina una medicion por su ID"""
    try:
        return controll.delete_measurement_sample(measurement_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

#----------------------------------------------------------
# Metodos WebSocket
#----------------------------------------------------------
@app.websocket("/ws/measurements")
async def websocket_endpoint(websocket: WebSocket):
    await ws_controller.handle_connection(websocket)

#----------------------------------------------------------
# Metodos del sistema
#----------------------------------------------------------
def init_system():
    """Inicializa el sistema"""
    print("=" * 60)
    print("\033[32m Iniciando sistema... \033[0m")
    print("=" * 60)

def open_browser():
    """Abre automáticamente el navegador"""
    url = "http://localhost:8000/app"
    print(f"\nAbriendo navegador en: {url}")
    #webbrowser.open(url)

if __name__ == "__main__":
    init_system()
    
    threading.Timer(2.0, open_browser).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

#agregar modos de descarga, seleccionar datos para visualizar individualmente en el historico, poder visualizar las fechas y hora de las mediciones para poder seleccionar cual historico revizar, que muestre por dia, mes, por año para poder ver los identificadores y descargar los datos en una hoja de datos con los parametros seleccionados, conservar la tabla para poder ver los datos en ese momento aparte de las graficas en una interfaz distinta 
#Poner el boton de inicio para empezar a guardar los datos o despues del guardado poner una opcion para poder ver que datos se guardan
