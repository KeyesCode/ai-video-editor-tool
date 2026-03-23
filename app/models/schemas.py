from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    segments: list[TranscriptSegment]
    full_text: str
    duration: float


class EditDecision(BaseModel):
    action: Literal["keep", "cut"]
    start: float
    end: float
    reason: str


class EditPlan(BaseModel):
    source_file: str
    decisions: list[EditDecision]
    output_duration: float
    task_type: Literal["cut_to_short", "edit_longform"]


class StitchSegment(BaseModel):
    source_index: int
    start: float
    end: float
    order: int


class StitchPlan(BaseModel):
    source_files: list[str]
    segments: list[StitchSegment]
    output_type: Literal["short", "longform"]


class JobStatus(BaseModel):
    job_id: str
    status: Literal[
        "pending",
        "extracting_audio",
        "transcribing",
        "analyzing",
        "editing",
        "complete",
        "failed",
    ] = "pending"
    progress: float = 0.0
    output_path: str | None = None
    error: str | None = None
