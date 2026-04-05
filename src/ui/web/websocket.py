"""WebSocket handler for real-time progress updates."""

import asyncio
import json
import threading
from src.utils.logger import get_logger
from src.config.manager import load_config

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

    class WebSocketDisconnect(Exception):
        """Fallback disconnect error when FastAPI is unavailable."""

    class WebSocket:  # pragma: no cover - typing fallback only
        """Fallback websocket type when FastAPI is unavailable."""

    class _DummyRouter:
        def websocket(self, *_args, **_kwargs):
            def _decorator(func):
                return func

            return _decorator

    APIRouter = _DummyRouter  # type: ignore[assignment]

logger = get_logger(__name__)

router = APIRouter()
_connected_clients = {}
_lock = threading.Lock()
_event_loop = None


def _get_configured_api_token():
    cfg = load_config()
    web_cfg = getattr(cfg, "web", None)
    return getattr(web_cfg, "api_token", None) if web_cfg else None


def _extract_supplied_token(websocket: WebSocket):
    authorization = websocket.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    x_api_token = websocket.headers.get("x-api-token")
    if x_api_token:
        return x_api_token.strip()
    qp_token = websocket.query_params.get("token")
    if qp_token:
        return qp_token.strip()
    return None


async def _require_ws_auth(websocket: WebSocket):
    configured_token = _get_configured_api_token()
    if not configured_token:
        return True
    supplied_token = _extract_supplied_token(websocket)
    if supplied_token == configured_token:
        return True
    await websocket.close(code=1008)
    return False


def get_connected_clients():
    with _lock:
        return dict(_connected_clients)


def set_event_loop(loop):
    global _event_loop
    with _lock:
        _event_loop = loop


def get_event_loop():
    with _lock:
        return _event_loop


def add_client(client_id, websocket):
    with _lock:
        _connected_clients[client_id] = websocket


def remove_client(client_id):
    with _lock:
        _connected_clients.pop(client_id, None)


@router.websocket("/progress")
async def progress_websocket(websocket: WebSocket):
    if not await _require_ws_auth(websocket):
        return
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
    except WebSocketDisconnect:
        remove_client(client_id)
    except Exception:
        logger.debug("WebSocket progress error")
        remove_client(client_id)


@router.websocket("/queue")
async def queue_websocket(websocket: WebSocket):
    if not await _require_ws_auth(websocket):
        return
    await websocket.accept()
    set_event_loop(asyncio.get_running_loop())
    client_id = str(id(websocket))
    add_client(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            _ = json.loads(data)
    except WebSocketDisconnect:
        remove_client(client_id)
    except Exception:
        logger.debug("WebSocket queue error")
        remove_client(client_id)


async def broadcast_progress(task_id, progress_data):
    message = json.dumps({"type": "progress", "task_id": task_id, **progress_data})
    clients = get_connected_clients()
    disconnected = []
    for client_id, client in clients.items():
        try:
            await client.send_text(message)
        except Exception:
            disconnected.append(client_id)
    for client_id in disconnected:
        remove_client(client_id)
