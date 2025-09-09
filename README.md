# Project GOS

This repository contains a minimal FastAPI backend and Streamlit UI.

## Running locally with Docker Compose

The included compose file starts both the API and UI services.

```bash
docker compose -f ops/docker-compose.yml up
```

- API available at: http://localhost:8000/health
- UI available at: http://localhost:8501
