# Nexaris Backend

Quick notes for deploying on Render:

- Render by default runs `gunicorn your_application.wsgi` which is for WSGI/Django apps.
- This project is FastAPI (ASGI). Add a `Procfile` to tell Render to start `uvicorn` instead.

Procfile contents:

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
