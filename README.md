# Nexaris Backend

Quick notes for deploying on Render:

- Render by default runs `gunicorn your_application.wsgi` which is for WSGI/Django apps.
This project is FastAPI (ASGI). Render sometimes expects a WSGI entrypoint and may try to run `gunicorn` by default. Two robust options:

- Use `gunicorn` with the `uvicorn` worker (recommended for Render):

```
web: gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT --workers 1
```

- Or run `uvicorn` directly (development-friendly):

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Environment variables (set these in Render's dashboard, not in the repo):

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

Local start (development):

```
.venv\Scripts\python.exe -m uvicorn main:app --reload
```
