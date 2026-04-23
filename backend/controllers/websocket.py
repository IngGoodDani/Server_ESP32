from    fastapi     import FastAPI, WebSocket, WebSocketDisconnect
from    pydantic    import BaseModel
from    fastapi.responses import HTMLResponse
from    models.measurement  import  Measurement

class CL_WEBSOCKET:

    def __init__(self, obj_db, obj_controll):
        # Lista de clientes conectados
        self.active_connections: List[WebSocket] = []
        self.obj_db = obj_db
        self.obj_controll = obj_controll

    async def connect(self, websocket: WebSocket):
        # Aceptar conexión del cliente
        await websocket.accept()
        self.active_connections.append(websocket)
        #print("Cliente conectado")

    def disconnect(self, websocket: WebSocket):
        # Remover cliente de la lista
        self.active_connections.remove(websocket)
        #print("Cliente desconectado")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        # Enviar mensaje a un solo cliente
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        # Enviar mensaje a todos los clientes conectados
        for connection in self.active_connections:
            await connection.send_json(message)

    async def handle_connection(self, websocket: WebSocket):
        # Manejo principal de la conexión

        await self.connect(websocket)

        try:
            while True:
                # Esperar datos del cliente
                json_response = await websocket.receive_json()
                
                event = json_response.get("event")
                data = json_response.get("data")
                print(f"\033[32mEVENT\033[0m:    {event}")

                match event:
                    case "esp32_data":
                        # ====== EVENTO: enviar datos ESP32 ======
                        response = self.handle_esp32_data(data)
                        await websocket.send_json(response)
    
                        measurement = self.obj_controll.get_data()
                        await self.broadcast(measurement)
                    
                    case "status_measurement":
                        # ====== EVENTO: consulta de estatus ======
                        if self.obj_db.current_measurement_id is None:
                            response = {
                                "event": "reponse_status_measurement", "measuring": False
                            }
                            await websocket.send_json(response)
                        else:
                            response = {
                                "event": "reponse_status_measurement", "measuring": True
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
                        response = self.obj_controll.get_sampl_time()
                    
                    case _:
                        response = {
                            "status": "rejected", "message": "Evento no valido"
                        }
                        await websocket.send_json(response)
                # Aquí puedes:
                # - Validar datos
                # - Guardar en base de datos
                # - Procesar lógica

        except WebSocketDisconnect:
            self.disconnect(websocket)
            
    # ====== LÓGICA (reutilizas lo que ya tenías) ======

    def handle_esp32_data(self, data: Measurement):
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