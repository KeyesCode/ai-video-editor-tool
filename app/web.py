import os
import shutil
import uuid
from pathlib import Path
from threading import Thread

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from config import settings
from app.models.schemas import JobStatus
from app.pipeline.runner import PipelineRunner

app = FastAPI(title="CookVid - AI Video Editor")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
runner = PipelineRunner(settings)

UPLOAD_DIR = Path(settings.output_dir) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

jobs: dict[str, JobStatus] = {}


def _save_upload(upload: UploadFile) -> str:
    """Save uploaded file and return path."""
    filename = f"{uuid.uuid4().hex}_{upload.filename}"
    path = UPLOAD_DIR / filename
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(path)


def _job_callback(job_id: str):
    """Create a callback that updates the jobs dict."""
    def callback(status: JobStatus):
        jobs[job_id] = status
    return callback


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "jobs": jobs,
    })


@app.post("/api/jobs/cut-to-short")
async def create_cut_to_short(video: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id=job_id, status="pending")

    video_path = _save_upload(video)

    def run():
        cb = _job_callback(job_id)
        try:
            result = runner.cut_to_short(video_path, callback=cb)
            jobs[job_id].status = "complete"
            jobs[job_id].output_path = result
            jobs[job_id].progress = 1.0
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error = str(e)

    Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@app.post("/api/jobs/stitch")
async def create_stitch(
    videos: list[UploadFile] = File(...),
    output_type: str = Form("longform"),
):
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id=job_id, status="pending")

    video_paths = [_save_upload(v) for v in videos]

    def run():
        cb = _job_callback(job_id)
        try:
            result = runner.stitch(video_paths, output_type, callback=cb)
            jobs[job_id].status = "complete"
            jobs[job_id].output_path = result
            jobs[job_id].progress = 1.0
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error = str(e)

    Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@app.post("/api/jobs/edit-longform")
async def create_edit_longform(video: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id=job_id, status="pending")

    video_path = _save_upload(video)

    def run():
        cb = _job_callback(job_id)
        try:
            result = runner.edit_longform(video_path, callback=cb)
            jobs[job_id].status = "complete"
            jobs[job_id].output_path = result
            jobs[job_id].progress = 1.0
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error = str(e)

    Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}, 404
    return jobs[job_id].model_dump()


@app.get("/api/jobs/{job_id}/download")
async def download_result(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}, 404
    job = jobs[job_id]
    if job.status != "complete" or not job.output_path:
        return {"error": "Job not complete"}, 400
    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        filename=Path(job.output_path).name,
    )
