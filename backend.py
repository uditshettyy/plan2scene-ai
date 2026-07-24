"""
backend.py — Plan2Scene AI FastAPI Backend

Endpoints:
  POST /api/process   — accepts a floor plan image, runs YOLO + pipeline, returns GLB URL
  GET  /api/status/{job_id} — poll job status
  GET  /models/{filename}   — serve generated GLB files

Usage:
  python backend.py
  (runs on http://localhost:8000)
"""

import os
import uuid
import shutil
import subprocess
import threading
import time
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ─── paths ──────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent.resolve()
OUTPUTS   = BASE_DIR / "outputs"
FRONTEND_MODELS = BASE_DIR / "frontend" / "public" / "models"
PYTHON    = BASE_DIR / "venv" / "Scripts" / "python.exe"

OUTPUTS.mkdir(exist_ok=True)
FRONTEND_MODELS.mkdir(parents=True, exist_ok=True)

# ─── job store (in-memory, per server restart) ──────────────────────────────
jobs: dict[str, dict] = {}   # job_id -> {status, message, glb_url, error}

# ─── app ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Plan2Scene AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated GLB files directly
app.mount("/models", StaticFiles(directory=str(FRONTEND_MODELS)), name="models")


# ─── processing worker ───────────────────────────────────────────────────────
def run_pipeline_worker(job_id: str, image_path: Path):
    jobs[job_id]["status"] = "running"
    jobs[job_id]["message"] = "Running YOLO inference..."

    detections_path = OUTPUTS / f"{job_id}_detections.json"
    job_out_dir     = OUTPUTS / f"job_{job_id}"
    job_out_dir.mkdir(parents=True, exist_ok=True)

    # Copy image so inference.py can use a known path
    working_image = BASE_DIR / f"_job_{job_id}_input.png"
    shutil.copy(image_path, working_image)

    try:
        # ── Step 1: YOLO inference ──────────────────────────────────────
        inference_script = BASE_DIR / "backend_inference.py"
        result = subprocess.run(
            [str(PYTHON), str(inference_script),
             str(working_image), str(detections_path)],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if result.returncode != 0:
            raise RuntimeError(f"Inference failed:\n{result.stderr}")

        jobs[job_id]["message"] = "Building wall graph and rooms..."

        # ── Step 2: Reconstruction pipeline ────────────────────────────
        result = subprocess.run(
            [str(PYTHON), str(BASE_DIR / "reconstruction" / "run_pipeline.py"),
             str(detections_path), str(job_out_dir),
             "10.0", "40.0", "80.0"],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if result.returncode != 0:
            raise RuntimeError(f"Pipeline failed:\n{result.stderr}")

        # ── Step 3: Copy GLB to frontend models ────────────────────────
        src_glb = job_out_dir / "plan2scene_vector_house.glb"
        dst_glb = FRONTEND_MODELS / f"{job_id}.glb"
        if src_glb.exists():
            shutil.copy(src_glb, dst_glb)
            # Also overwrite the default model
            shutil.copy(src_glb, FRONTEND_MODELS / "plan2scene_vector_house.glb")
        else:
            raise RuntimeError("Pipeline completed but no GLB was produced.")

        jobs[job_id]["status"]  = "done"
        jobs[job_id]["message"] = "3D model ready!"
        jobs[job_id]["glb_url"] = f"/models/{job_id}.glb"
        jobs[job_id]["log"]     = result.stdout

    except Exception as e:
        jobs[job_id]["status"]  = "error"
        jobs[job_id]["message"] = str(e)
    finally:
        # Clean up temp files
        working_image.unlink(missing_ok=True)
        image_path.unlink(missing_ok=True)


# ─── routes ─────────────────────────────────────────────────────────────────

@app.post("/api/process")
async def process_floorplan(file: UploadFile = File(...)):
    """Accept an uploaded floor plan image, start the pipeline, return a job_id."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted.")

    job_id = str(uuid.uuid4())[:8]
    ext    = Path(file.filename).suffix or ".png"
    tmp    = OUTPUTS / f"upload_{job_id}{ext}"

    # Save upload
    content = await file.read()
    tmp.write_bytes(content)

    # Register job
    jobs[job_id] = {
        "status":  "queued",
        "message": "Queued...",
        "glb_url": None,
        "log":     "",
    }

    # Run in background thread so we don't block the HTTP response
    thread = threading.Thread(target=run_pipeline_worker, args=(job_id, tmp), daemon=True)
    thread.start()

    return JSONResponse({"job_id": job_id, "status": "queued"})


@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    """Poll the status of a running pipeline job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JSONResponse(jobs[job_id])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
