# Web API Reference

## Launch
```bash
kyro web              # Default port 8000
kyro web --port 9000  # Custom port
```

## REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Server status |
| POST | `/api/download` | Start a download |
| GET | `/api/queue` | Get queue status |
| POST | `/api/queue/clear` | Clear completed downloads |
| GET | `/api/stats` | Get download statistics |
| GET | `/api/files` | List downloaded files |

## WebSocket
- `GET /ws/progress` - Real-time download progress updates
- `GET /ws/queue` - Real-time queue status updates

## CORS
- Configurable via `config.yaml` under `web.cors_origins`
- Default: `["*"]`
