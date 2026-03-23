import subprocess
import tempfile
from pathlib import Path

from app.models.schemas import EditPlan, StitchPlan


def _get_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return float(result.stdout.strip())


def _extract_segment(video_path: str, start: float, end: float, output_path: str):
    """Extract a segment from a video using FFmpeg."""
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg segment extraction failed: {result.stderr[-500:]}")


def _concat_segments(segment_files: list[str], output_path: str):
    """Concatenate segment files using FFmpeg concat demuxer."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg_file in segment_files:
            f.write(f"file '{seg_file}'\n")
        concat_list = f.name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    Path(concat_list).unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {result.stderr[-500:]}")


def execute_edit(plan: EditPlan, output_path: str) -> str:
    """Execute an edit plan (cut-to-short or longform cleanup) using FFmpeg."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    keep_segments = [d for d in plan.decisions if d.action == "keep"]
    keep_segments.sort(key=lambda d: d.start)

    if not keep_segments:
        raise ValueError("Edit plan has no segments to keep")

    duration = _get_duration(plan.source_file)
    tmp_dir = Path(tempfile.mkdtemp())
    segment_files = []

    try:
        for i, seg in enumerate(keep_segments):
            start = max(0, seg.start)
            end = min(duration, seg.end)
            if end > start:
                seg_path = str(tmp_dir / f"seg_{i:04d}.mp4")
                _extract_segment(plan.source_file, start, end, seg_path)
                segment_files.append(seg_path)

        if not segment_files:
            raise ValueError("No valid segments after timestamp validation")

        if len(segment_files) == 1:
            Path(segment_files[0]).rename(output_path)
        else:
            _concat_segments(segment_files, output_path)
    finally:
        for f in segment_files:
            Path(f).unlink(missing_ok=True)
        tmp_dir.rmdir()

    return output_path


def execute_stitch(plan: StitchPlan, output_path: str) -> str:
    """Execute a stitch plan combining segments from multiple videos."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    durations = {i: _get_duration(f) for i, f in enumerate(plan.source_files)}
    sorted_segments = sorted(plan.segments, key=lambda s: s.order)

    tmp_dir = Path(tempfile.mkdtemp())
    segment_files = []

    try:
        for i, seg in enumerate(sorted_segments):
            src_file = plan.source_files[seg.source_index]
            src_duration = durations[seg.source_index]
            start = max(0, seg.start)
            end = min(src_duration, seg.end)
            if end > start:
                seg_path = str(tmp_dir / f"seg_{i:04d}.mp4")
                _extract_segment(src_file, start, end, seg_path)
                segment_files.append(seg_path)

        if not segment_files:
            raise ValueError("No valid segments to stitch")

        if len(segment_files) == 1:
            Path(segment_files[0]).rename(output_path)
        else:
            _concat_segments(segment_files, output_path)
    finally:
        for f in segment_files:
            Path(f).unlink(missing_ok=True)
        tmp_dir.rmdir()

    return output_path
