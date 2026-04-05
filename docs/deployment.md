# Deployment Guide

## Docker
docker-compose -f docker/docker-compose.yml up -d

## Systemd
See docs/ for systemd service file.

## Production
- Use nginx reverse proxy
- Enable HTTPS
- Set KYRO_WEB__DEBUG=false
- Configure rate limiting
