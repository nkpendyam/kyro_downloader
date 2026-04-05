FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -c "import yt_dlp; print(f'yt-dlp installed')"

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/* && groupadd -r kyro && useradd -r -g kyro -d /app -s /sbin/nologin kyro
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app
RUN mkdir -p /app/downloads /app/logs /app/config && chown -R kyro:kyro /app
VOLUME ["/app/downloads", "/app/config", "/app/logs"]
ENV KYRO_WEB_HOST=0.0.0.0
ENV KYRO_WEB_PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
USER kyro
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]
