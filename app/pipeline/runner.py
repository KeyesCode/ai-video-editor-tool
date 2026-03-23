import os
import uuid
from pathlib import Path
from typing import Callable

from config import Settings
from app.models.schemas import JobStatus
from app.pipeline.audio import extract_audio
from app.pipeline.transcribe import transcribe
from app.pipeline.analyze import analyze_for_short, analyze_for_stitch, analyze_for_longform
from app.pipeline.edit import execute_edit, execute_stitch


class PipelineRunner:
    def __init__(self, config: Settings):
        self.config = config

    def _update(self, job: JobStatus, status: str, progress: float, callback: Callable | None):
        job.status = status
        job.progress = progress
        if callback:
            callback(job)

    def _default_output(self, input_path: str, suffix: str) -> str:
        name = Path(input_path).stem
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        return str(out_dir / f"{name}_{suffix}.mp4")

    def cut_to_short(
        self,
        video_path: str,
        output_path: str | None = None,
        callback: Callable | None = None,
    ) -> str:
        job = JobStatus(job_id=str(uuid.uuid4()))
        output_path = output_path or self._default_output(video_path, "short")

        try:
            self._update(job, "extracting_audio", 0.1, callback)
            audio_path = extract_audio(video_path)

            self._update(job, "transcribing", 0.3, callback)
            transcript = transcribe(audio_path, self.config.whisper_model)

            self._update(job, "analyzing", 0.5, callback)
            plan = analyze_for_short(
                transcript, video_path, self.config.anthropic_api_key,
                self.config.min_short_duration, self.config.max_short_duration,
            )

            self._update(job, "editing", 0.7, callback)
            result = execute_edit(plan, output_path)

            self._update(job, "complete", 1.0, callback)
            job.output_path = result
            os.unlink(audio_path)
            return result

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            if callback:
                callback(job)
            raise

    def stitch(
        self,
        video_paths: list[str],
        output_type: str = "longform",
        output_path: str | None = None,
        callback: Callable | None = None,
    ) -> str:
        job = JobStatus(job_id=str(uuid.uuid4()))
        output_path = output_path or self._default_output(video_paths[0], f"stitched_{output_type}")

        try:
            self._update(job, "extracting_audio", 0.1, callback)
            audio_paths = [extract_audio(v) for v in video_paths]

            self._update(job, "transcribing", 0.3, callback)
            transcripts = [
                transcribe(a, self.config.whisper_model)
                for a in audio_paths
            ]

            self._update(job, "analyzing", 0.5, callback)
            plan = analyze_for_stitch(
                transcripts, video_paths, self.config.anthropic_api_key,
                output_type, self.config.min_short_duration, self.config.max_short_duration,
            )

            self._update(job, "editing", 0.7, callback)
            result = execute_stitch(plan, output_path)

            self._update(job, "complete", 1.0, callback)
            job.output_path = result
            for a in audio_paths:
                os.unlink(a)
            return result

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            if callback:
                callback(job)
            raise

    def edit_longform(
        self,
        video_path: str,
        output_path: str | None = None,
        callback: Callable | None = None,
    ) -> str:
        job = JobStatus(job_id=str(uuid.uuid4()))
        output_path = output_path or self._default_output(video_path, "edited")

        try:
            self._update(job, "extracting_audio", 0.1, callback)
            audio_path = extract_audio(video_path)

            self._update(job, "transcribing", 0.3, callback)
            transcript = transcribe(audio_path, self.config.whisper_model)

            self._update(job, "analyzing", 0.5, callback)
            plan = analyze_for_longform(
                transcript, video_path, self.config.anthropic_api_key,
            )

            self._update(job, "editing", 0.7, callback)
            result = execute_edit(plan, output_path)

            self._update(job, "complete", 1.0, callback)
            job.output_path = result
            os.unlink(audio_path)
            return result

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            if callback:
                callback(job)
            raise
