---
title: Graduation project
emoji: 🚗
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# Graduation project — YOLO + plate OCR

Dockerized [Gradio](https://gradio.app) app using [Ultralytics YOLO](https://docs.ultralytics.com) for **object boxes** and **[EasyOCR](https://github.com/JaidedAI/EasyOCR)** (`ar` + `en`) to read **plate numbers and letters** (Arabic and Latin) on Egyptian-style plates.

YOLO alone usually does **not** label each digit/letter; OCR is what decodes the plate text.

## Add your weights

1. Put your trained file in this folder as **`yolo8_last_version_car(must).pt`**  
   (or **`best.pt`** / **`last.pt`**, which are also detected automatically).

2. For large files on Hugging Face, use **Git LFS** from this directory:

   ```bash
   git lfs install
   git lfs track "*.pt"
   git add .gitattributes yolo8_last_version_car\(must\).pt
   git commit -m "Add YOLO weights"
   git push
   ```

   Or upload the `.pt` via the Space **Files** tab on [the Space page](https://huggingface.co/spaces/Karty12345/Graduation_project).

3. Optional: set env **`YOLO_WEIGHTS`** to an absolute path inside the container if you use a custom filename.

## Local test

```bash
cd huggingface-space
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:7860**.

### No `.pt` file yet?

The app tries **local** weights first, then **`yolov8n.pt`** → **`yolov8s.pt`** → **`yolov8m.pt`** (Ultralytics may download the first time — needs network). **Plate reading uses EasyOCR even if YOLO fails.**

`YOLO_STRICT=1` only logs a notice; the UI **no longer crashes** if weights are missing — YOLO is skipped and OCR runs on the full image.

### Pip: `hf-gradio` vs `gradio-client`

That warning appears when **`hf-gradio`** is installed in the same environment as **Gradio 5** (they want different `gradio-client` versions). This Space does **not** need `hf-gradio`. In your venv run:

```bash
pip uninstall hf-gradio -y
```

Use a **fresh venv** only for `huggingface-space` to avoid clashes with other tools.

If both `opencv-python` and `opencv-python-headless` are installed, keep one:

```bash
pip uninstall opencv-python -y
```

### OCR tuning (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `OCR_CONF` | `0.08` | Minimum confidence for a text box (lower = more detections, more noise). |
| `OCR_MIN_SIDE` | `720` | Upscale so the **shortest** image side is at least this many pixels before OCR. |
| `MAX_DISPLAY` | `1600` | Downscale output if the longest side exceeds this (keeps the UI fast). |
| `OCR_GPU` | off | Set to `1` on a GPU machine to speed up EasyOCR. |

## Deploy to Hugging Face

Use this folder as the **root** of the Space repository (not the whole monorepo):

```bash
cd huggingface-space
git init
git remote add origin https://huggingface.co/spaces/Karty12345/Graduation_project
git add app.py requirements.txt Dockerfile README.md .dockerignore .gitignore
git commit -m "Deploy AI Space"
git push -u origin main
```

Add your `.pt` (and `.gitattributes` if using LFS) before or after the first push.
