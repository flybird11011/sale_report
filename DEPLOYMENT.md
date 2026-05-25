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

Use the sample config in `deploy/nginx/report.zaza.de5.net.conf`.

It serves:

- `http://report.zaza.de5.net` on port `80`
- `https://report.zaza.de5.net` on port `443`

Traffic on `80` is redirected to `https`.

The HTTPS server block expects a certificate and key mounted into the container at:

- `/etc/nginx/certs/report.zaza.de5.net.pem`
- `/etc/nginx/certs/report.zaza.de5.net.key`

For Cloudflare, the easiest path is to create an Origin Certificate and install it on the VPS.

The proxy target should be `http://sales-report:5000`.

If your existing port 80 service is itself running in Docker, connect it to the same `webproxy` network:

```bash
docker network connect webproxy exam-nginx
docker restart exam-nginx
```

After that, `exam-nginx` can resolve `sales-report` by container name.

## Example nginx container mount

If you manage the proxy container yourself, mount both the config and the certificate directory:

```bash
docker run -d \
  --name exam-nginx \
  --network webproxy \
  -p 80:80 \
  -p 443:443 \
  -v /opt/exam_bank/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v /opt/exam_bank/certs:/etc/nginx/certs:ro \
  nginx:1.27-alpine
```

If you use Docker Compose for the proxy, add the same volume mounts and expose both ports.

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
- For Cloudflare `Full (strict)`, make sure the origin certificate is installed before switching the mode on.
