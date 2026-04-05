# Web API Reference

## Launch
```bash
kyro web              # Default port 8000
kyro web --port 9000  # Custom port
```

## REST Endpoints

## Authentication

When `web.api_token` is configured, all `/api/*` endpoints require authentication.

Supported auth methods:
- `Authorization: Bearer <token>`
- `X-API-Token: <token>`

Without a valid token, API requests return `401 Unauthorized`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Server status |
| POST | `/api/download` | Start a download |
| POST | `/api/batch` | Queue multiple URLs |
| POST | `/api/playlist` | Start playlist download |
| GET | `/api/queue` | Get queue status |
| POST | `/api/queue/{task_id}/pause` | Pause a queued/running task |
| POST | `/api/queue/{task_id}/resume` | Resume a paused task |
| DELETE | `/api/queue/{task_id}` | Cancel or remove a task |
| GET | `/api/status/{task_id}` | Get status for one task |
| GET | `/api/info?url=...` | Fetch video metadata + formats |
| GET | `/api/platforms` | List supported platforms |
| GET | `/api/config` | Get runtime config (sensitive values redacted) |
| PUT | `/api/config` | Update one config key |
| GET | `/api/files/` | List downloaded files/folders |
| GET | `/api/files/download/{filename:path}` | Download a file from downloads dir |
| DELETE | `/api/files/{filename:path}` | Delete a file or folder |

### Request body: `/api/download`
```json
{
	"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
	"output_path": "downloads",
	"format_id": "bestvideo+bestaudio",
	"only_audio": false,
	"quality": "best",
	"hdr": false,
	"dolby": false,
	"audio_format": "mp3",
	"audio_quality": "192",
	"audio_selector": null,
	"priority": "normal",
	"subtitles": {
		"enabled": true,
		"languages": ["en", "es"],
		"embed": false,
		"auto_generated": true,
		"format": "srt"
	},
	"sponsorblock": false,
	"preset": "none",
	"output_template": "%(uploader)s/%(title)s [%(id)s].%(ext)s"
}
```

### Request body: `/api/playlist`
```json
{
	"url": "https://www.youtube.com/playlist?list=...",
	"output_path": "downloads",
	"only_audio": false,
	"quality": "1080p",
	"audio_format": "mp3",
	"audio_quality": "192",
	"subtitles": false,
	"sponsorblock": false
}
```

### Request body: `/api/config`
```json
{
	"section": "general",
	"key": "output_path",
	"value": "downloads"
}
```

## WebSocket
- `GET /ws/progress` - Real-time download progress updates
- `GET /ws/queue` - Real-time queue status updates

When `web.api_token` is configured, websocket connections also require auth.
You can pass token using:
- `Authorization: Bearer <token>` header
- `X-API-Token: <token>` header
- `?token=<token>` query parameter

WebSocket clients can send:
- `{"type":"subscribe"}` to confirm a progress subscription
- `{"type":"ping"}` to receive `{"type":"pong"}` health responses

## CORS
- Configurable via `config.yaml` under `web.cors_origins`
- Default: `["*"]`
