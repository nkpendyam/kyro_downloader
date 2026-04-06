"""WebSocket handler for real-time progress updates."""

import asyncio
import json
import threading
import time
from typing import Any

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
_connected_clients: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()
_event_loop: asyncio.AbstractEventLoop | None = None
_CLIENT_TTL_SECONDS = 3600
_MAX_CONNECTIONS = 50
_SEND_TIMEOUT_SECONDS = 5.0
_MESSAGE_RATE_LIMIT = 10
_MESSAGE_RATE_WINDOW = 1.0
_MAX_MESSAGE_SIZE = 1_048_576


def _get_configured_api_token() -> str | None:
    """Return configured API token if set."""
    cfg = load_config()
    web_cfg = getattr(cfg, "web", None)
    return getattr(web_cfg, "api_token", None) if web_cfg else None


def _extract_supplied_token(websocket: WebSocket) -> str | None:
    """Extract auth token from websocket headers."""
    ws_protocol = websocket.headers.get("sec-websocket-protocol", "")
    if ws_protocol:
        for candidate in ws_protocol.split(","):
            token_candidate = candidate.strip()
            if token_candidate.lower().startswith("bearer "):
                return token_candidate[7:].strip()
            if token_candidate:
                return token_candidate

    authorization = websocket.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    x_api_token = websocket.headers.get("x-api-token")
    if x_api_token:
        return x_api_token.strip()
    return None


async def _require_ws_auth(websocket: WebSocket) -> bool:
    """Reject connection if auth token is required but missing/invalid."""
    configured_token = _get_configured_api_token()
    if not configured_token:
        return True
    supplied_token = _extract_supplied_token(websocket)
    if supplied_token == configured_token:
        return True
    logger.warning("WebSocket auth rejected: missing or invalid Authorization/Sec-WebSocket-Protocol token")
    await websocket.close(code=1008)
    return False


def get_connected_clients() -> dict[str, dict[str, Any]]:
    """Return a snapshot of connected clients."""
    with _lock:
        return dict(_connected_clients)


def cleanup_stale_clients() -> int:
    """Remove disconnected or expired clients. Return count removed."""
    now = time.time()
    stale_ids: list[str] = []
    with _lock:
        for client_id, entry in _connected_clients.items():
            websocket = entry.get("websocket")
            connected_at = float(entry.get("connected_at", now))
            if websocket is None:
                stale_ids.append(client_id)
                continue
            if str(getattr(websocket, "client_state", "")).endswith("DISCONNECTED"):
                stale_ids.append(client_id)
                continue
            if now - connected_at > _CLIENT_TTL_SECONDS:
                stale_ids.append(client_id)
        for client_id in stale_ids:
            _connected_clients.pop(client_id, None)
    for client_id in stale_ids:
        logger.debug(f"Removed stale websocket client: {client_id}")
    return len(stale_ids)


def set_event_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    """Set or clear the global event loop reference."""
    global _event_loop
    with _lock:
        _event_loop = loop


def get_event_loop() -> asyncio.AbstractEventLoop | None:
    """Return the current event loop reference."""
    with _lock:
        return _event_loop


def clear_event_loop_if_stopped() -> None:
    """Clear the event loop reference if it is no longer running."""
    global _event_loop
    with _lock:
        if _event_loop is not None and not _event_loop.is_running():
            _event_loop = None


def get_active_connection_count() -> int:
    """Return the number of active WebSocket connections."""
    with _lock:
        return len(_connected_clients)


def _check_connection_limit() -> bool:
    """Return True if a new connection would exceed the limit."""
    with _lock:
        return len(_connected_clients) >= _MAX_CONNECTIONS


def add_client(client_id: str, websocket: WebSocket) -> None:
    """Register a new WebSocket client."""
    with _lock:
        _connected_clients[client_id] = {
            "websocket": websocket,
            "connected_at": time.time(),
            "message_times": [],
        }


def remove_client(client_id: str) -> None:
    """Remove a WebSocket client."""
    with _lock:
        _connected_clients.pop(client_id, None)


def _check_message_rate(client_id: str) -> bool:
    """Return True if the client is within message rate limits."""
    now = time.time()
    with _lock:
        entry = _connected_clients.get(client_id)
        if entry is None:
            return False
        message_times: list[float] = entry.get("message_times", [])
        cutoff = now - _MESSAGE_RATE_WINDOW
        message_times[:] = [t for t in message_times if t >= cutoff]
        message_times.append(now)
        entry["message_times"] = message_times
        return len(message_times) <= _MESSAGE_RATE_LIMIT


@router.websocket("/progress")
async def progress_websocket(websocket: WebSocket):
    """Handle real-time progress updates via WebSocket."""
    if _check_connection_limit():
        await websocket.close(code=1013, reason="Too many connections")
        return
    if not await _require_ws_auth(websocket):
        return
    await websocket.accept()
    set_event_loop(asyncio.get_running_loop())
    client_id = str(id(websocket))
    add_client(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > _MAX_MESSAGE_SIZE:
                logger.warning(f"WebSocket message too large from {client_id}")
                continue
            if not _check_message_rate(client_id):
                continue
            message = json.loads(data)
            if message.get("type") == "subscribe":
                await websocket.send_json({"type": "subscribed", "client_id": client_id})
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("WebSocket progress error")
    finally:
        remove_client(client_id)
        clear_event_loop_if_stopped()


@router.websocket("/queue")
async def queue_websocket(websocket: WebSocket):
    """Handle real-time queue status updates via WebSocket."""
    if _check_connection_limit():
        await websocket.close(code=1013, reason="Too many connections")
        return
    if not await _require_ws_auth(websocket):
        return
    await websocket.accept()
    set_event_loop(asyncio.get_running_loop())
    client_id = str(id(websocket))
    add_client(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > _MAX_MESSAGE_SIZE:
                continue
            if not _check_message_rate(client_id):
                continue
            _ = json.loads(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("WebSocket queue error")
    finally:
        remove_client(client_id)
        clear_event_loop_if_stopped()


async def broadcast_progress(task_id: str, progress_data: dict[str, Any]) -> None:
    """Broadcast progress update to all connected clients with per-client timeout."""
    cleanup_stale_clients()
    message = json.dumps({"type": "progress", "task_id": task_id, **progress_data})
    clients = get_connected_clients()
    disconnected: list[str] = []
    for client_id, entry in clients.items():
        client = entry.get("websocket")
        if client is None:
            disconnected.append(client_id)
            continue
        try:
            await asyncio.wait_for(client.send_text(message), timeout=_SEND_TIMEOUT_SECONDS)
        except (asyncio.TimeoutError, Exception):
            disconnected.append(client_id)
    for client_id in disconnected:
        remove_client(client_id)
