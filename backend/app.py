from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from PIL import Image
import io
import json
import os
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import torch
    from torchvision import models, transforms
except Exception:  # noqa: BLE001
    torch = None
    models = None
    transforms = None

app = FastAPI(title="Tire Analyzer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TireClassifier:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.model_path = model_dir / "tire_classifier.pt"
        self.meta_path = model_dir / "tire_classifier.meta.json"

        self._loaded = False
        self._load_error: Optional[str] = None
        self._device = None
        self._model = None
        self._class_names: list[str] = []
        self._image_size = 224
        self._preprocess = None

    @property
    def available(self) -> bool:
        return self._loaded

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def try_load(self) -> None:
        if self._loaded:
            return
        if torch is None or models is None or transforms is None:
            self._load_error = "torch/torchvision not installed; using dummy analysis."
            return
        if not self.model_path.exists() or not self.meta_path.exists():
            self._load_error = "No trained model found; using dummy analysis."
            return

        try:
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self._class_names = list(meta["class_names"])
            self._image_size = int(meta.get("image_size", 224))

            # Must match training script.
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            model = models.mobilenet_v3_small(weights=weights)
            in_features = model.classifier[-1].in_features
            model.classifier[-1] = torch.nn.Linear(in_features, len(self._class_names))

            state = torch.load(self.model_path, map_location="cpu")
            model.load_state_dict(state)
            model.eval()

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)

            normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            preprocess = transforms.Compose(
                [
                    transforms.Resize(self._image_size + 32),
                    transforms.CenterCrop(self._image_size),
                    transforms.ToTensor(),
                    normalize,
                ]
            )

            self._device = device
            self._model = model
            self._preprocess = preprocess
            self._loaded = True
            self._load_error = None
        except Exception as exc:  # noqa: BLE001
            self._load_error = f"Failed to load model: {exc}"

    def predict(self, image: Image.Image) -> dict:
        self.try_load()
        if not self._loaded:
            raise RuntimeError(self._load_error or "Model not loaded")

        x = self._preprocess(image).unsqueeze(0)
        x = x.to(self._device)
        with torch.no_grad():
            logits = self._model(x)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        top_idx = int(np.argmax(probs))
        label = self._class_names[top_idx]
        confidence = float(probs[top_idx])

        return {
            "label": label,
            "confidence": confidence,
            "probabilities": {self._class_names[i]: float(probs[i]) for i in range(len(self._class_names))},
            "model": {"arch": "mobilenet_v3_small", "image_size": self._image_size},
        }


def _to_decision(ml_result: dict) -> dict:
    """Map ML output to OK vs REPLACE decision with a user-friendly message."""
    label = ml_result.get("label", "")
    confidence = ml_result.get("confidence", 0.0)
    
    # New Kaggle dataset classes: "Cracked" and "Normal".
    # Anything marked as "Cracked" implies the tire is heavily worn.
    is_defect = label.lower() == "cracked"

    if is_defect:
        decision = "REPLACE"
        message = "Severe cracking or damage detected. Consider replacing the tire soon for safety."
    else:
        decision = "OK"
        message = "Tire appears to be in normal condition. Keep monitoring tread depth and pressure regularly."

    return {
        **ml_result,
        "decision": decision,
        "message": message,
    }


MODEL_DIR = Path(os.environ.get("TIRE_MODEL_DIR", Path(__file__).parent / "models"))
classifier = TireClassifier(MODEL_DIR)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    # Simple landing page for quick manual testing
    classifier.try_load()
    model_status = "loaded" if classifier.available else "not loaded"
    model_detail = classifier.load_error or ""
    return """
    <html>
      <head>
        <title>Tire Analyzer</title>
      </head>
      <body>
        <h1>Tire Analyzer</h1>
        <p>Upload a photo of your car's tire to get a basic assessment.</p>
        <p><b>Model:</b> """ + model_status + """</p>
        <p><small>""" + model_detail + """</small></p>
        <form action="/analyze" enctype="multipart/form-data" method="post">
          <input name="file" type="file" accept="image/*">
          <button type="submit">Analyze</button>
        </form>
      </body>
    </html>
    """


def _basic_dummy_analysis(image: Image.Image) -> dict:
    """
    Placeholder analysis function.

    For now, it just checks image size and returns a fake assessment.
    Replace this later with real ML-based analysis.
    """
    width, height = image.size

    if width < 200 or height < 200:
        status = "uncertain"
        message = "Image is too small for reliable analysis. Please retake a closer photo of the tire."
    else:
        status = "ok"
        message = "Tire appears okay in this basic demo. A real model may give a different answer."

    return {
        "status": status,
        "message": message,
        "image_width": width,
        "image_height": height,
    }


@app.post("/analyze")
async def analyze_tire(file: UploadFile = File(...)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    contents = await file.read()

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc

    # Prefer the trained classifier if available; otherwise fall back to dummy logic.
    try:
        ml = classifier.predict(image)
        analysis = _to_decision({"status": "ml", **ml})
        return {"filename": file.filename, "analysis": analysis}
    except Exception:
        result = _basic_dummy_analysis(image)
        return {"filename": file.filename, "analysis": result}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

