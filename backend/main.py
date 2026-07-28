import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


REPO_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_DIR = REPO_ROOT / "uploads"
OUTPUTS_DIR = REPO_ROOT / "outputs_by_job"
INFERENCE_SCRIPT = REPO_ROOT / "models" / "inference.py"
RUN_PIPELINE_SCRIPT = REPO_ROOT / "reconstruction" / "run_pipeline.py"

UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

DEFAULT_SNAP_TOL = 6.0
DEFAULT_BRIDGE_TOL = 90.0
DEFAULT_MAX_ASSIGN_DIST = 80.0

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


JOBS: dict[str, dict] = {}


def new_job_record() -> dict:
    return {
        "status": "queued",      
        "created_at": datetime.now(timezone.utc).isoformat(),
        "log": [],
        "error": None,
    }


def log(job_id: str, message: str):
    print(f"[job {job_id}] {message}")
    if job_id in JOBS:
        JOBS[job_id]["log"].append(message)



def run_subprocess(job_id: str, cmd: list[str]) -> None:
    log(job_id, f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        [str(c) for c in cmd], capture_output=True, text=True
    )
    if result.stdout:
        for line in result.stdout.splitlines():
            log(job_id, line)
    if result.returncode != 0:
        if result.stderr:
            for line in result.stderr.splitlines():
                log(job_id, line)
        raise RuntimeError(f"Command failed (exit {result.returncode}): {' '.join(str(c) for c in cmd)}")


def build_inference_command(input_image: Path, detections_out: Path) -> list[str]:
    """
    Confirmed via manual testing: the default confidence (0.25) was
    silently dropping real wall detections (16 walls found vs 22 at
    conf=0.15 on the same image) -- using 0.15 here to match.
    """
    return [
        sys.executable, str(INFERENCE_SCRIPT),
        "--input", str(input_image),
        "--output", str(detections_out),
        "--conf", "0.15",
    ]


def process_job(
    job_id: str,
    input_image: Path,
    snap_tol: float,
    bridge_tol: float,
    max_assign_dist: float,
) -> None:
    job_out_dir = OUTPUTS_DIR / job_id
    job_out_dir.mkdir(parents=True, exist_ok=True)
    detections_path = job_out_dir / "v2_detections.json"

    try:
        JOBS[job_id]["status"] = "detecting"
        run_subprocess(job_id, build_inference_command(input_image, detections_path))

        if not detections_path.exists():
            raise RuntimeError(
                f"Inference reported success but {detections_path} was not created "
                f"-- check build_inference_command()'s assumed CLI flags against "
                f"your actual models/inference.py."
            )

        JOBS[job_id]["status"] = "reconstructing"
        run_subprocess(job_id, [
            sys.executable, str(RUN_PIPELINE_SCRIPT),
            str(detections_path), str(job_out_dir),
            snap_tol, bridge_tol, max_assign_dist,
        ])

        glb_path = job_out_dir / "plan2scene_vector_house.glb"
        if not glb_path.exists():
            raise RuntimeError(f"Pipeline reported success but {glb_path} was not created.")

        JOBS[job_id]["status"] = "done"
        log(job_id, "Job complete.")

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        log(job_id, f"FAILED: {e}")


app = FastAPI(title="Plan2Scene-AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    log: list[str]
    error: Optional[str] = None
    model_url: Optional[str] = None
    detections_url: Optional[str] = None


@app.post("/api/plans", response_model=JobCreatedResponse)
async def upload_plan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    snap_tol: float = DEFAULT_SNAP_TOL,
    bridge_tol: float = DEFAULT_BRIDGE_TOL,
    max_assign_dist: float = DEFAULT_MAX_ASSIGN_DIST,
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    job_id = str(uuid.uuid4())
    job_dir = UPLOADS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = job_dir / f"input{ext}"

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    JOBS[job_id] = new_job_record()
    log(job_id, f"Uploaded {file.filename} -> {input_path}")

    background_tasks.add_task(
        process_job, job_id, input_path, snap_tol, bridge_tol, max_assign_dist
    )

    return JobCreatedResponse(job_id=job_id, status="queued")


@app.get("/api/plans/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "Unknown job_id")

    model_url = f"/api/plans/{job_id}/model" if job["status"] == "done" else None
    detections_path = OUTPUTS_DIR / job_id / "v2_detections.json"
    detections_url = f"/api/plans/{job_id}/detections" if detections_path.exists() else None

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        log=job["log"],
        error=job["error"],
        model_url=model_url,
        detections_url=detections_url,
    )


@app.get("/api/plans/{job_id}/model")
async def get_job_model(job_id: str):
    glb_path = OUTPUTS_DIR / job_id / "plan2scene_vector_house.glb"
    if not glb_path.exists():
        raise HTTPException(404, "Model not ready yet (or job failed) -- check /api/plans/{job_id} first")
    return FileResponse(glb_path, media_type="model/gltf-binary", filename="house.glb")


@app.get("/api/plans/{job_id}/detections")
async def get_job_detections(job_id: str):
    detections_path = OUTPUTS_DIR / job_id / "v2_detections.json"
    if not detections_path.exists():
        raise HTTPException(404, "Detections not ready yet -- check /api/plans/{job_id} first")
    return FileResponse(detections_path, media_type="application/json")


@app.get("/api/health")
async def health():
    return {"status": "ok"}