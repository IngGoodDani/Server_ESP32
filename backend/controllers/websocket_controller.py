from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

class WebSocketController:

    def __init__(self):
        # Lista de clientes conectados
        self.active_connections: List[WebSocket] = []

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