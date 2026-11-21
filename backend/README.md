# Tire Analyzer API

Dataset download, training, Docker, and the recorded validation accuracy are documented in the [repository README](../README.md).

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

`GET /health` returns `{"status":"ok"}`. `POST /analyze` accepts a multipart image in the form field `file`.

`TIRE_MODEL_DIR` overrides the weights directory (default: `models/` next to `app.py`).
