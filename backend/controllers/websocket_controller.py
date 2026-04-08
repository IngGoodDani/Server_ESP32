from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

class WebSocketController:

    def __init__(self, db):
        # Lista de clientes conectados
        self.active_connections: List[WebSocket] = []
        self.db = db

    async def connect(self, websocket: WebSocket):
        # Aceptar conexión del cliente
        await websocket.accept()
        self.active_connections.append(websocket)
        print("Cliente conectado")

    def disconnect(self, websocket: WebSocket):
        # Remover cliente de la lista
        self.active_connections.remove(websocket)
        print("Cliente desconectado")

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
                data = await websocket.receive_json()
                print(f"Datos recibidos: {data}")
                
                event = data.get("event")
                payload = data.get("data")
                print(f"Data: {payload}")

                # ====== EVENTO: enviar datos ESP32 ======
                if event == "esp32_data":
                    response = self.handle_esp32_data(payload)
                    await websocket.send_json(response)

                    # Opcional: mandar a todos (dashboard)
                    await self.broadcast({
                        "event": "new_measurement",
                        "data": payload
                    })

                # Aquí puedes:
                # - Validar datos
                # - Guardar en base de datos
                # - Procesar lógica

                # Reenviar a todos (broadcast)
                await self.broadcast({
                    "event": "new_measurement",
                    "data": data
                })

        except WebSocketDisconnect:
            self.disconnect(websocket)
            
    # ====== LÓGICA (reutilizas lo que ya tenías) ======

    def handle_esp32_data(self, data):
        try:
            if self.db.current_measurement_id is None:
                return {
                    "event": "esp32_data_response",
                    "status": "rejected",
                    "message": "No hay una medición activa"
                }

            sample_index = self.db.save_measurement(data)

            return {
                "event": "esp32_data_response",
                "status": "ok",
                "measurement_id": self.db.current_measurement_id,
                "sample_index": sample_index,
                "total_samples": self.db.measurement_sample_counter
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
                "measuring": self.db.current_measurement_id is not None
            }

        except Exception as e:
            return {
                "event": "status_measurement_response",
                "status": "error",
                "message": str(e)
            }