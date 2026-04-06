# Web API Reference

## Launch
```bash
kyro web              # Default port 8000
kyro web --port 9000  # Custom port
```

## REST Endpoints

## Authentication

When `web.api_token` is configured, all API endpoints require authentication.

Supported auth methods:
- `Authorization: Bearer <token>`
- `X-API-Token: <token>`

Without a valid token, API requests return `401 Unauthorized`.

### API Versioning

- Primary API prefix: `/api/v1/*`
- Legacy compatibility prefix: `/api/*`
- Legacy `/api/*` responses include deprecation headers:
  - `Deprecation: true`
  - `Link: </api/v1>; rel="successor-version"`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/status` | Server status |
| POST | `/api/v1/download` | Start a download |
| POST | `/api/v1/batch` | Queue multiple URLs |
| POST | `/api/v1/playlist` | Start playlist download |
| GET | `/api/v1/queue` | Get queue status |
| POST | `/api/v1/queue/{task_id}/pause` | Pause a queued/running task |
| POST | `/api/v1/queue/{task_id}/resume` | Resume a paused task |
| DELETE | `/api/v1/queue/{task_id}` | Cancel or remove a task |
| GET | `/api/v1/status/{task_id}` | Get status for one task |
| GET | `/api/v1/info?url=...` | Fetch video metadata + formats |
| GET | `/api/v1/platforms` | List supported platforms |
| GET | `/api/v1/config` | Get runtime config (sensitive values redacted) |
| PUT | `/api/v1/config` | Update one config key |
| GET | `/api/v1/files/` | List downloaded files/folders |
| GET | `/api/v1/files/download/{filename:path}` | Download a file from downloads dir |
| DELETE | `/api/v1/files/{filename:path}` | Delete a file or folder |
| GET | `/api/status` | Legacy server status (deprecated) |
| POST | `/api/download` | Legacy start download (deprecated) |
| POST | `/api/batch` | Legacy batch queue (deprecated) |
| POST | `/api/playlist` | Legacy playlist start (deprecated) |
| GET | `/api/queue` | Legacy queue status (deprecated) |
| POST | `/api/queue/{task_id}/pause` | Legacy pause task (deprecated) |
| POST | `/api/queue/{task_id}/resume` | Legacy resume task (deprecated) |
| DELETE | `/api/queue/{task_id}` | Legacy cancel/remove task (deprecated) |
| GET | `/api/status/{task_id}` | Legacy task status (deprecated) |
| GET | `/api/info?url=...` | Legacy metadata lookup (deprecated) |
| GET | `/api/platforms` | Legacy platform list (deprecated) |
| GET | `/api/config` | Legacy runtime config (deprecated) |
| PUT | `/api/config` | Legacy config update (deprecated) |
| GET | `/api/files/` | Legacy file listing (deprecated) |
| GET | `/api/files/download/{filename:path}` | Legacy file download (deprecated) |
| DELETE | `/api/files/{filename:path}` | Legacy file delete (deprecated) |

### Request body: `/api/v1/download`
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

### Request body: `/api/v1/playlist`
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

### Request body: `/api/v1/config`
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

WebSocket clients can send:
- `{"type":"subscribe"}` to confirm a progress subscription
- `{"type":"ping"}` to receive `{"type":"pong"}` health responses

## CORS
- Configurable via `config.yaml` under `web.cors_origins`
- Default: `["*"]`
