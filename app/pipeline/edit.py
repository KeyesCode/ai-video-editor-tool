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


def _build_filter_complex(num_segments: int) -> str:
    """Build FFmpeg filter_complex string to normalize and concat segments."""
    filters = []
    for i in range(num_segments):
        # Scale to 1080p, handle rotation, normalize pixel format, set framerate
        filters.append(
            f"[{i}:v:0]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,"
            f"format=yuv420p[v{i}]"
        )
        filters.append(f"[{i}:a:0]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")

    # concat needs interleaved: [v0][a0][v1][a1]...
    interleaved = "".join(f"[v{i}][a{i}]" for i in range(num_segments))
    filters.append(f"{interleaved}concat=n={num_segments}:v=1:a=1[outv][outa]")

    return ";".join(filters)


def _extract_and_concat(segments: list[tuple[str, float, float]], output_path: str):
    """Extract segments from source videos and concatenate in one FFmpeg call."""
    if not segments:
        raise ValueError("No segments to process")

    cmd = ["ffmpeg", "-y"]

    # Add inputs with trim points
    for src_file, start, end in segments:
        cmd.extend(["-ss", str(start), "-t", str(end - start), "-i", src_file])

    # Build and add filter_complex
    filter_str = _build_filter_complex(len(segments))
    cmd.extend([
        "-filter_complex", filter_str,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr[-1000:]}")


def execute_edit(plan: EditPlan, output_path: str) -> str:
    """Execute an edit plan (cut-to-short or longform cleanup) using FFmpeg."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    keep_segments = [d for d in plan.decisions if d.action == "keep"]
    keep_segments.sort(key=lambda d: d.start)

    if not keep_segments:
        raise ValueError("Edit plan has no segments to keep")

    duration = _get_duration(plan.source_file)
    segments = []
    for seg in keep_segments:
        start = max(0, seg.start)
        end = min(duration, seg.end)
        if end > start:
            segments.append((plan.source_file, start, end))

    if not segments:
        raise ValueError("No valid segments after timestamp validation")

    _extract_and_concat(segments, output_path)
    return output_path


def execute_stitch(plan: StitchPlan, output_path: str) -> str:
    """Execute a stitch plan combining segments from multiple videos."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    durations = {i: _get_duration(f) for i, f in enumerate(plan.source_files)}
    sorted_segments = sorted(plan.segments, key=lambda s: s.order)

    segments = []
    for seg in sorted_segments:
        src_file = plan.source_files[seg.source_index]
        src_duration = durations[seg.source_index]
        start = max(0, seg.start)
        end = min(src_duration, seg.end)
        if end > start:
            segments.append((src_file, start, end))

    if not segments:
        raise ValueError("No valid segments to stitch")

    _extract_and_concat(segments, output_path)
    return output_path
