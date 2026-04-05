# Deployment Guide

## Docker
docker-compose -f docker/docker-compose.yml up -d

The container defaults to starting the Web UI/API:
- `python -m src.main --ui web --host 0.0.0.0 --port 8000`

Environment overrides must use double-underscore nested keys, for example:
- `KYRO_WEB__HOST=0.0.0.0`
- `KYRO_WEB__PORT=8000`
- `KYRO_WEB__DEBUG=false`
- `KYRO_GENERAL__LOG_LEVEL=INFO`

## Systemd
See docs/ for systemd service file.

## Production
- Use nginx reverse proxy
- Enable HTTPS
- Set KYRO_WEB__DEBUG=false
- Configure rate limiting
