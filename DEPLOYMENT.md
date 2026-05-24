# Report Deployment Guide

This project is ready to run as a Dockerized Flask app behind a reverse proxy for `report.zaza.de5.net`.

## What gets persisted

- `./data/uploads`
- `./data/output`
- `./data/saved_mappings.json`

These live outside the container so they survive restarts and image rebuilds.

## Build and run

```bash
docker network inspect webproxy >/dev/null 2>&1 || docker network create webproxy
docker compose up -d --build
```

The app will listen on `127.0.0.1:5000` on the VPS and also join the shared Docker network named `webproxy`.

## Reverse proxy

Use the sample config in `deploy/nginx/report.zaza.de5.net.conf` and point it to `http://sales-report:5000`.

If your existing port 80 service is itself running in Docker, connect it to the same `webproxy` network:

```bash
docker network connect webproxy exam-nginx
docker restart exam-nginx
```

After that, `exam-nginx` can resolve `sales-report` by container name.

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
- If you rebuild the app container later, keep it attached to `webproxy` and leave `exam-nginx` on the same network.
