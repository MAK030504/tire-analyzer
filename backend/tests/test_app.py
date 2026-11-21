"""API and preprocessing checks that do not need the dataset or weights."""

import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app import TireClassifier, _to_decision, app
from train_classifier import build_transforms


class AnalyzeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_analyze_requires_file(self) -> None:
        response = self.client.post("/analyze")
        self.assertEqual(response.status_code, 422)

    def test_analyze_rejects_non_image_content_type(self) -> None:
        response = self.client.post(
            "/analyze",
            files={"file": ("notes.txt", b"not a tire", "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.json()["detail"].lower())

    def test_analyze_rejects_invalid_image_bytes(self) -> None:
        response = self.client.post(
            "/analyze",
            files={"file": ("bad.png", b"this is not an image", "image/png")},
        )
        self.assertEqual(response.status_code, 400)

    def test_analyze_tiny_generated_image_uses_size_fallback(self) -> None:
        payload = _png_bytes(width=16, height=16, color=(255, 0, 0))
        response = self.client.post(
            "/analyze",
            files={"file": ("tiny.png", payload, "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["filename"], "tiny.png")
        analysis = body["analysis"]
        self.assertEqual(analysis["status"], "uncertain")
        self.assertEqual(analysis["image_width"], 16)
        self.assertEqual(analysis["image_height"], 16)
        self.assertNotIn("label", analysis)

    def test_analyze_larger_generated_image_is_ok_without_weights(self) -> None:
        payload = _jpeg_bytes(width=220, height=210, color=(20, 80, 40))
        response = self.client.post(
            "/analyze",
            files={"file": ("tire.jpg", payload, "image/jpeg")},
        )
        self.assertEqual(response.status_code, 200)
        analysis = response.json()["analysis"]
        self.assertEqual(analysis["status"], "ok")
        self.assertEqual(analysis["image_width"], 220)
        self.assertEqual(analysis["image_height"], 210)


class DecisionTests(unittest.TestCase):
    def test_cracked_maps_to_replace(self) -> None:
        result = _to_decision({"label": "Cracked", "confidence": 0.91, "status": "ml"})
        self.assertEqual(result["decision"], "REPLACE")
        self.assertEqual(result["label"], "Cracked")

    def test_normal_maps_to_ok(self) -> None:
        result = _to_decision({"label": "Normal", "confidence": 0.8, "status": "ml"})
        self.assertEqual(result["decision"], "OK")
        self.assertEqual(result["label"], "Normal")


class ClassifierLoadTests(unittest.TestCase):
    def test_missing_weights_do_not_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            classifier = TireClassifier(Path(tmp))
            classifier.try_load()
            self.assertFalse(classifier.available)
            self.assertTrue(classifier.load_error)


class PreprocessTests(unittest.TestCase):
    def test_val_preprocess_on_tiny_generated_image(self) -> None:
        _, val_tfms = build_transforms(224)
        image = Image.new("RGB", (8, 8), color=(255, 0, 0))
        tensor = val_tfms(image)

        self.assertEqual(tuple(tensor.shape), (3, 224, 224))
        # Solid red, then ImageNet normalization. Resize and center-crop keep a flat color.
        expected_r = (1.0 - 0.485) / 0.229
        expected_g = (0.0 - 0.456) / 0.224
        expected_b = (0.0 - 0.406) / 0.225
        self.assertAlmostEqual(float(tensor[0, 0, 0]), expected_r, places=4)
        self.assertAlmostEqual(float(tensor[1, 0, 0]), expected_g, places=4)
        self.assertAlmostEqual(float(tensor[2, 0, 0]), expected_b, places=4)
        self.assertTrue(bool(tensor.isfinite().all()))

    def test_train_preprocess_outputs_model_input_shape(self) -> None:
        train_tfms, _ = build_transforms(224)
        image = Image.new("RGB", (12, 9), color=(10, 20, 30))
        tensor = train_tfms(image)
        self.assertEqual(tuple(tensor.shape), (3, 224, 224))
        self.assertTrue(bool(tensor.isfinite().all()))


def _png_bytes(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg_bytes(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
