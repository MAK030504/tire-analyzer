# Tire Analyzer

Portfolio sample of a tire-photo classifier. A FastAPI service accepts an image and labels it **Cracked** or **Normal** with a MobileNetV3-Small network trained in PyTorch. Cracked maps to a `REPLACE` decision. Normal maps to `OK`. A React upload page in `frontend/` calls the same API.

The weights file and the image dataset are local only. This repository keeps the API, the trainer, and both Dockerfiles.

## Accuracy

`backend/models/tire_classifier.meta.json` records the validation accuracy saved with the original checkpoint:

**`best_val_acc`: 0.9560975609756097**

`train_classifier.py` writes that field when it stores the best `tire_classifier.pt`. The score is accuracy on the trainer's random validation split (default `--val_split 0.2`, `--seed 42`). A separate test-set accuracy is not recorded in this repository.

After a new training run, replace the number above with `best_val_acc` from the updated `backend/models/tire_classifier.meta.json`.

## Dataset

The images used for the recorded checkpoint come from the Kaggle dataset [Tire Texture Image Recognition](https://www.kaggle.com/datasets/jehanbhathena/tire-texture-image-recognition) (`jehanbhathena/tire-texture-image-recognition`). `backend/download_kaggle_data.py` downloads it with `kagglehub` and copies every `.jpg`, `.jpeg`, and `.png` into class folders.

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install kagglehub
python download_kaggle_data.py
```

The script writes:

- `backend/data/Cracked/`
- `backend/data/Normal/`

`train_classifier.py` reads an ImageFolder layout (`class_name/image.jpg`) from `--data_dir`. Run the downloader from `backend/` so those two folders land on `data/`.

If `kagglehub` asks you to sign in, create a Kaggle API token and save it as `~/.kaggle/kaggle.json`. That file is gitignored.

`backend/convert_yolo_to_classification.py` is a separate path for a YOLO tree named `tire_defects_datasets` in the script. It expects `data.yaml` plus a `train`, `valid`, or `test` split that contains `images/` and `labels/`, and it writes an ImageFolder directory (default `converted_dataset/`). The checkpoint metadata lists `Cracked` and `Normal`, which are the Kaggle classes above.

## Train

From `backend/`, after `data/Cracked` and `data/Normal` exist:

```bash
python train_classifier.py --data_dir data --out_dir models
```

Defaults are 8 epochs, batch size 16, learning rate `3e-4`, validation split `0.2`, image size 224, and seed 42. The script keeps the MobileNetV3-Small backbone, replaces the final linear layer with one unit per class folder, and uses ImageNet normalization. It writes:

- `models/tire_classifier.pt` (state dict, gitignored)
- `models/tire_classifier.meta.json` (`arch`, `image_size`, `class_names`, `best_val_acc`)

The metadata file in this repository is the record from the original training run. A new run overwrites both files on disk.

## Run the API

From `backend/`:

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

- `GET /health` returns `{"status":"ok"}`.
- `GET /` is a small upload form.
- `POST /analyze` takes a multipart file field named `file` and expects an image content type.

`TIRE_MODEL_DIR` selects the directory that holds `tire_classifier.pt` and `tire_classifier.meta.json`. The default is `backend/models`. With the weights file absent, `/analyze` still responds: it uses a size check (images smaller than 200×200 are marked uncertain) and does not return a Cracked/Normal label.

The React page, for local development:

```bash
cd frontend
npm install
npm run dev
```

Vite serves the UI on port 5173 and the page calls `http://localhost:8000`. Start the API first.

## Docker

`backend/Dockerfile` and `frontend/Dockerfile` are both real images. `docker-compose.yml` builds them together.

Place `tire_classifier.pt` in `backend/models/` before you rely on model predictions. Compose bind-mounts that directory to `/app/models`, so a file you add there is visible to the API without copying it into git. Without the weights, the API container still starts and `/analyze` uses the size-check fallback.

API image only:

```bash
docker build -t tire-analyzer-api ./backend
docker run --rm -p 8000:8000 tire-analyzer-api
```

API and frontend:

```bash
docker compose up --build
```

- API: [http://localhost:8000](http://localhost:8000)
- Frontend (nginx, with `/api` proxied to the API): [http://localhost](http://localhost)

The API image is `python:3.10-slim`. It installs `backend/requirements.txt`, copies `app.py` and `models/`, and runs `uvicorn app:app --host 0.0.0.0 --port 8000`. The frontend image builds the Vite app and serves `dist/` with nginx.

## Tests

From `backend/`:

```bash
python -m unittest discover -s tests -v
```

The tests build a tiny in-memory image, check the `/analyze` request rules, and run the validation preprocessing in `train_classifier.py`. They do not download the Kaggle dataset and they do not load `tire_classifier.pt`.

## License

[MIT](LICENSE)
