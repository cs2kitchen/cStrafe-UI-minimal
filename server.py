# server.py
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
from input_events import InputListener
from classifier import ShotResult

app = FastAPI()

# 确保 HTML 模板正确定义（放在文件顶部）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <title>cStrafe HUD</title>
        <style>
            body { 
                background-color: rgba(0, 0, 0, 0); 
                margin: 0; 
                overflow: hidden; 
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
            #container {
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                padding: 10px;
                text-shadow: 2px 2px 0px #000000;
            }
            .line { font-size: 24px; white-space: pre; }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div id="container">
            <div id="line1" class="line" style="color: white;">Waiting...</div>
            <div id="line2" class="line" style="color: white;"></div>
        </div>
        <script>
            var ws = new WebSocket("ws://" + location.host + "/ws");
            var container = document.getElementById("container");
            var l1 = document.getElementById("line1");
            var l2 = document.getElementById("line2");

            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                
                l1.style.color = data.color;
                l2.style.color = data.color;

                if (data.type === "Run&Gun") {
                    l1.innerText = "RUN & GUN";
                    l2.innerText = "";
                } else if (data.type === "Static") {
                    l1.innerText = "STATIC";
                    l2.innerText = "";
                } else {
                    var label = (data.type === "Overlap") ? "Overlap" : "Gap";
                    l1.innerText = label + " - " + data.diff + " ms";
                    l2.innerText = "Shot Delay - " + data.delay + " ms";
                }
            };
            
            ws.onclose = function() {
                setTimeout(function() {
                    location.reload();
                }, 1000);
            };
        </script>
    </body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(data))

manager = ConnectionManager()

listener = None

@app.get("/")
async def get():
    return HTMLResponse(HTML_TEMPLATE)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def broadcast_shot(result: ShotResult):
    if manager:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(result.to_display_data()), 
            loop
        )

loop = None

def start_server():
    global loop, listener
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    listener = InputListener(on_shot_callback=broadcast_shot)
    listener.start()
    
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    try:
        loop.run_until_complete(server.serve())
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()

if __name__ == "__main__":
    start_server()
