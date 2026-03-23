from app.models.schemas import Transcript

SYSTEM_PROMPT = """You are a professional cooking video editor specializing in assembling cohesive videos
from multiple source clips. Your job is to analyze video metadata and any available transcripts to determine
the best ordering and assembly of clips into a polished final video.

IMPORTANT: Many cooking videos have minimal or no speech — they are visual. Do NOT discard clips just because
they have no transcript. A clip with no speech is likely showing an important cooking action (chopping, searing,
plating, etc.) and should be included.

You must return ONLY valid JSON matching the exact schema specified."""


def build_prompt(
    transcripts: list[Transcript],
    video_durations: list[float] | None = None,
    filenames: list[str] | None = None,
    output_type: str = "longform",
    min_short: int = 30,
    max_short: int = 60,
) -> str:
    total_duration = 0.0
    all_info = []

    for i, t in enumerate(transcripts):
        dur = video_durations[i] if video_durations else t.duration
        total_duration += dur
        fname = filenames[i] if filenames else f"video_{i}"

        info = f"\n--- VIDEO {i}: {fname} (duration: {dur:.1f}s) ---"
        if t.segments and t.full_text.strip():
            for s in t.segments:
                info += f"\n[{s.start:.1f}s - {s.end:.1f}s] {s.text}"
        else:
            info += "\n[No speech detected - visual cooking content only]"

        all_info.append(info)

    clips_text = "\n".join(all_info)

    if output_type == "short":
        duration_instruction = f"""Create a SHORT video ({min_short}-{max_short} seconds total).
Pick the most visually impactful moments across all videos. The final result should feel like
a highlight reel with a strong hook, key action, and satisfying conclusion."""
    else:
        duration_instruction = f"""Create a LONG-FORM video that combines ALL source clips.
The total source duration is {total_duration:.1f}s. Your output should be close to this total.

CRITICAL RULES FOR LONG-FORM:
- Include EVERY video clip. Do not skip any clip.
- For each clip, include the FULL duration (start: 0, end: full duration) unless there is
  a clear reason to trim (e.g., accidental recording, blank screen).
- Clips with no speech are VISUAL cooking content — include them fully.
- Your job is primarily to determine the best ORDER, not to cut content.
- Order clips to create a logical cooking narrative: prep -> cook -> plate -> serve.
- If the original filename order makes sense (sequential numbering), preserve it."""

    return f"""Assemble these {len(transcripts)} cooking video clips into a cohesive {output_type} video.

{clips_text}

TASK:
{duration_instruction}

Return JSON in this exact format:
{{
    "segments": [
        {{
            "source_index": <which video 0-indexed>,
            "start": <start_seconds>,
            "end": <end_seconds>,
            "order": <position in final output, 0-indexed>
        }}
    ],
    "output_type": "{output_type}"
}}

RULES:
- source_index must be a valid video index (0 to {len(transcripts) - 1})
- Timestamps must fall within the source video's duration
- Order field determines the final sequence (0 = first segment played)
- For clips with no transcript, use start: 0 and end: <full clip duration>"""
