# Report VPS Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the Excel report app so it can run in Docker on a VPS and be reverse-proxied at `report.zaza.de5.net`.

**Architecture:** Keep the Flask app as the single backend service, run it with Gunicorn inside a container, and persist uploads/output/mapping state on a mounted data directory. Expose the service on localhost port 5000 and route traffic from the existing reverse proxy to the container.

**Tech Stack:** Flask, pandas, openpyxl, xlrd, Gunicorn, Docker, Docker Compose, Nginx-style reverse proxy.

---

### Task 1: Make the app container-friendly

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update paths to be environment-driven**

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', BASE_DIR)
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(DATA_DIR, 'uploads'))
OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(DATA_DIR, 'output'))
MAPPINGS_FILE = os.environ.get('MAPPINGS_FILE', os.path.join(DATA_DIR, 'saved_mappings.json'))
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')
```

- [ ] **Step 2: Use the absolute index path and env-based host/port**

```python
@app.route('/')
def index():
    return send_file(INDEX_FILE)

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug)
```

- [ ] **Step 3: Verify syntax**

Run: `python -m py_compile app.py`
Expected: no output and exit code 0

### Task 2: Add packaging files

**Files:**
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: Add pinned dependencies**

```txt
Flask==3.0.3
Flask-Cors==4.0.1
gunicorn==22.0.0
pandas==2.2.2
openpyxl==3.1.5
xlrd==2.0.1
```

- [ ] **Step 2: Add a production Docker image**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data/uploads /data/output
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "180", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

- [ ] **Step 3: Add compose with persistent data volume**

```yaml
services:
  sales-report:
    build:
      context: .
    container_name: sales-report
    restart: unless-stopped
    environment:
      DATA_DIR: /data
      UPLOAD_FOLDER: /data/uploads
      OUTPUT_FOLDER: /data/output
      MAPPINGS_FILE: /data/saved_mappings.json
      PORT: "5000"
      HOST: "0.0.0.0"
      FLASK_DEBUG: "0"
    volumes:
      - ./data:/data
    ports:
      - "127.0.0.1:5000:5000"
```

- [ ] **Step 4: Ignore build artifacts and sample files**

```gitignore
__pycache__/
*.pyc
*.pyo
*.xlsx
*.xls
output/
uploads/
data/
.git/
```

- [ ] **Step 5: Verify the image builds**

Run: `docker compose build`
Expected: image builds successfully without missing-package errors

### Task 3: Add reverse proxy and operator docs

**Files:**
- Create: `deploy/nginx/report.zaza.de5.net.conf`
- Create: `DEPLOYMENT.md`

- [ ] **Step 1: Add a reverse proxy example**

```nginx
server {
    listen 80;
    server_name report.zaza.de5.net;

    client_max_body_size 100m;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }
}
```

- [ ] **Step 2: Document the deployment flow**

```md
docker compose up -d --build
```

Explain the persistent data directory and how to point the existing reverse proxy at `127.0.0.1:5000`.

- [ ] **Step 3: Sanity check the docs**

Verify the document references match the actual file names and ports used by the compose file.
