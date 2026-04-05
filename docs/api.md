# API Reference

## Base URL
http://localhost:8000/api

## Endpoints
- POST /api/download - Queue a download
- POST /api/batch - Queue multiple downloads
- POST /api/playlist - Download a full playlist
- GET /api/status - Get overall status
- GET /api/status/{task_id} - Get task status
- GET /api/queue - Get download queue
- POST /api/queue/{task_id}/pause - Pause a task
- POST /api/queue/{task_id}/resume - Resume a task
- DELETE /api/queue/{task_id} - Cancel a task
- GET /api/info?url= - Get video info
- GET /api/platforms - List platforms
- GET /api/config - Get configuration
- PUT /api/config - Update configuration

## WebSocket
Connect to ws://localhost:8000/ws/progress for real-time progress updates.
