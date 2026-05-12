from    fastapi     import FastAPI, WebSocket, WebSocketDisconnect
from    pydantic    import BaseModel
from    fastapi.responses import HTMLResponse
from    models.measurement  import  Measurement
from    datetime    import datetime, date, time

class CL_WEBSOCKET:

    def __init__(self, obj_db, obj_controll):
        # Lista de clientes conectados
        self.esp32_connections: list[WebSocket] = []
        self.dashboard_connections: list[WebSocket] = []
        self.obj_db = obj_db
        self.obj_controll = obj_controll

    async def connect(self, websocket: WebSocket, client: str):
        # Aceptar conexion del cliente
        try:
            await websocket.accept()
            match client:
                case "dashboard":
                    self.dashboard_connections.append(websocket)
                case "esp32":
                    self.esp32_connections.append(websocket)
                case _:
                    return
            print(f"\033[32mCLIENT\033[0m:   {client}")
        except ValueError:
            pass

    def disconnect(self, websocket: WebSocket, client: str):
        # Remover conexion del cliente
        try:
            match client:
                case "dashboard":
                    self.dashboard_connections.remove(websocket)
                case "esp32":
                    self.esp32_connections.remove(websocket)
                case _:
                    return
            print(f"\033[31mCLIENT\033[0m:   {client}")
        except ValueError:
            pass

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        # Enviar mensaje a un solo cliente
        await websocket.send_json(message)

    async def broadcast(self, message: dict, client: str):
        # Enviar mensaje
        match client:
            case "dashboard":
                connections = self.dashboard_connections
            case "esp32":
                connections = self.esp32_connections
            case _:
                return
                
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
                
        for connection in disconnected:
            connections.remove(connection)

    async def handle_connection_dashboard(self, websocket: WebSocket):
        await self.connect(websocket, "dashboard")
        
        try:
            while True:
                # Esperar datos del cliente
                json_response = await websocket.receive_json()
                
                event = json_response.get("event")
                data = json_response.get("data")
                print(f"\033[32mEVENT\033[0m:    {event}")

                match event:
                    case "get_data":
                        measurement = self.obj_controll.get_data()
                        await websocket.send_json(self.sanitize(measurement))
                    
                    case "status_measurement":
                        # ====== EVENTO: consulta de estatus ======
                        if self.obj_db.current_measurement_id is None:
                            measuring = False
                        else:
                            measuring = True
                        
                        response = {
                            "event": "reponse_status_measurement", "measuring": measuring
                        }
                        await websocket.send_json(response)
                    
                    case "start_measurement":
                        # ====== EVENTO: inicia medición ======
                        response = self.obj_controll.start_measurement()
                        await websocket.send_json(response)
                    
                    case "end_measurement":
                        # ====== EVENTO: finaliza la medición ======
                        response = self.obj_controll.end_measurement()
                        await websocket.send_json(response)
                    
                    case "get_sample_time":
                        # ====== EVENTO: Consulta teimpo de medicion ======
                        response = self.obj_controll.get_sampling_time()
                        await websocket.send_json(response)
                    
                    case _:
                        response = {
                            "status": "rejected", "message": "Evento no valido"
                        }
                        await websocket.send_json(response)
                
        except WebSocketDisconnect:
            print(f"error {WebSocketDisconnect}")
            self.disconnect(websocket, "dashboard")

    async def handle_connection_esp32(self, websocket: WebSocket):
        # Manejo principal de la conexion al dashboard

        await self.connect(websocket, "esp32")

        try:
            while True:
                # Esperar datos del cliente
                json_response = await websocket.receive_json()
                
                event = json_response.get("event")
                data = json_response.get("data")
                print(f"\033[32mEVENT\033[0m:    {event}")

                match event:
                    case "esp32_data":
                        response = await self.handle_esp32_data(data)
                        await websocket.send_json(response)
                    
                    case "get_sample_time":
                        # ====== EVENTO: Consulta teimpo de medicion ======
                        response = self.obj_controll.get_sampling_time()
                        await websocket.send_json(response)
                    
                    case _:
                        response = {
                            "event": "error",
                            "status": "rejected",
                            "message": "Evento no valido"
                        }
                        await websocket.send_json(response)
        
        except WebSocketDisconnect:
            print(f"error {WebSocketDisconnect}")
            self.disconnect(websocket, "esp32")

    async def handle_esp32_data(self, data: Measurement):
        try:
            if self.obj_db.current_measurement_id is None:
                return {
                    "event": "esp32_data_response",
                    "status": "rejected",
                    "message": "No hay una medición activa"
                }

            measurements = Measurement(**data)
            #print(f"Data: {measurements}")
            sample_index = self.obj_db.save_measurement(measurements)
            
            measurement = self.obj_controll.get_data()
            await self.broadcast(self.sanitize(measurement), "dashboard")
            
            return {
                "event": "esp32_data_response",
                "status": "ok",
                "measurement_id": self.obj_db.current_measurement_id,
                "sample_index": sample_index,
                "total_samples": self.obj_db.measurement_sample_counter
            }

        except Exception as e:
            return {
                "event": "esp32_data_response",
                "status": "error",
                "message": str(e)
            }

    def handle_status(self):
        try:
            return {
                "event": "status_measurement_response",
                "status": "ok",
                "measuring": self.obj_db.current_measurement_id is not None
            }

        except Exception as e:
            return {
                "event": "status_measurement_response",
                "status": "error",
                "message": str(e)
            }
    
    def sanitize(self, obj):
        if isinstance(obj, dict):
            return {k: self.sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.sanitize(i) for i in obj]
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return obj