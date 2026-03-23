from pathlib import Path

from moviepy import VideoFileClip, concatenate_videoclips

from app.models.schemas import EditPlan, StitchPlan


def execute_edit(plan: EditPlan, output_path: str) -> str:
    """Execute an edit plan (cut-to-short or longform cleanup) using MoviePy."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    clip = VideoFileClip(plan.source_file)
    try:
        keep_segments = [d for d in plan.decisions if d.action == "keep"]
        keep_segments.sort(key=lambda d: d.start)

        if not keep_segments:
            raise ValueError("Edit plan has no segments to keep")

        subclips = []
        for seg in keep_segments:
            start = max(0, seg.start)
            end = min(clip.duration, seg.end)
            if end > start:
                subclips.append(clip.subclipped(start, end))

        if not subclips:
            raise ValueError("No valid subclips after timestamp validation")

        final = concatenate_videoclips(subclips, method="compose")
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        final.close()
    finally:
        clip.close()

    return output_path


def execute_stitch(plan: StitchPlan, output_path: str) -> str:
    """Execute a stitch plan combining segments from multiple videos."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    clips = []
    try:
        source_clips = {
            i: VideoFileClip(f) for i, f in enumerate(plan.source_files)
        }

        sorted_segments = sorted(plan.segments, key=lambda s: s.order)

        for seg in sorted_segments:
            src = source_clips[seg.source_index]
            start = max(0, seg.start)
            end = min(src.duration, seg.end)
            if end > start:
                clips.append(src.subclipped(start, end))

        if not clips:
            raise ValueError("No valid segments to stitch")

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        final.close()
    finally:
        for c in source_clips.values():
            c.close()

    return output_path
