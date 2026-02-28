# Tire Analyzer Backend

Simple FastAPI backend for the tire analyzer prototype.

## Setup

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the development server:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

4. Open the landing page in your browser:

```text
http://localhost:8000/
```

This will let you upload a tire image and see the dummy analysis result in JSON.

