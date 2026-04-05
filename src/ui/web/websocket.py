"""WebSocket handler for real-time progress updates."""
import asyncio
import json
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
_connected_clients = {}
_lock = threading.Lock()
_event_loop = None

def get_connected_clients():
    with _lock: return dict(_connected_clients)

def set_event_loop(loop):
    global _event_loop
    with _lock:
        _event_loop = loop

def get_event_loop():
    with _lock:
        return _event_loop

def add_client(client_id, websocket):
    with _lock: _connected_clients[client_id] = websocket

def remove_client(client_id):
    with _lock: _connected_clients.pop(client_id, None)

@router.websocket("/progress")
async def progress_websocket(websocket: WebSocket):
    await websocket.accept()
    set_event_loop(asyncio.get_running_loop())
    client_id = str(id(websocket))
    add_client(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "subscribe":
                await websocket.send_json({"type": "subscribed", "client_id": client_id})
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect: remove_client(client_id)
    except Exception: remove_client(client_id)

@router.websocket("/queue")
async def queue_websocket(websocket: WebSocket):
    await websocket.accept()
    set_event_loop(asyncio.get_running_loop())
    client_id = str(id(websocket))
    add_client(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            _ = json.loads(data)
    except WebSocketDisconnect: remove_client(client_id)
    except Exception: remove_client(client_id)

async def broadcast_progress(task_id, progress_data):
    message = json.dumps({"type": "progress", "task_id": task_id, **progress_data})
    clients = get_connected_clients()
    disconnected = []
    for client_id, client in clients.items():
        try: await client.send_text(message)
        except Exception: disconnected.append(client_id)
    for client_id in disconnected: remove_client(client_id)
