# Report Deployment Guide

This project is ready to run as a Dockerized Flask app behind a reverse proxy for `report.zaza.de5.net`.

## What gets persisted

- `./data/uploads`
- `./data/output`
- `./data/saved_mappings.json`

These live outside the container so they survive restarts and image rebuilds.

## Build and run

```bash
docker compose up -d --build
```

The app will listen on `127.0.0.1:5000` on the VPS.

## Reverse proxy

Use the sample config in `deploy/nginx/report.zaza.de5.net.conf` and point it to `http://127.0.0.1:5000`.

If your existing port 80 service is itself running in Docker, you have two common options:

1. Keep that proxy container on the host network or allow it to reach `127.0.0.1:5000`.
2. Put both containers on the same Docker network and change `proxy_pass` to the app service name.

## Files to upload on the VPS

- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `app.py`
- `index.html`
- `deploy/nginx/report.zaza.de5.net.conf`

## Notes

- The app uses `gunicorn` in production.
- The upload limit is controlled by the reverse proxy, so keep `client_max_body_size` high enough for your Excel files.
