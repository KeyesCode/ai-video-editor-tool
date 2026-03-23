from app.models.schemas import Transcript

SYSTEM_PROMPT = """You are a professional cooking video editor specializing in assembling cohesive videos
from multiple source clips. Your job is to analyze transcripts from multiple cooking videos and determine
the best segments and ordering to create a polished final video.

You must return ONLY valid JSON matching the exact schema specified."""


def build_prompt(
    transcripts: list[Transcript],
    output_type: str = "longform",
    min_short: int = 30,
    max_short: int = 60,
) -> str:
    all_segments = []
    for i, t in enumerate(transcripts):
        all_segments.append(f"\n--- VIDEO {i} (duration: {t.duration:.1f}s) ---")
        for s in t.segments:
            all_segments.append(f"[{s.start:.1f}s - {s.end:.1f}s] {s.text}")

    segments_text = "\n".join(all_segments)

    if output_type == "short":
        duration_instruction = f"""Create a SHORT video ({min_short}-{max_short} seconds total).
Pick only the most impactful moments across all videos. The final result should feel like
a highlight reel with a strong hook, key action, and satisfying conclusion."""
    else:
        duration_instruction = """Create a LONG-FORM video that combines the best content from all sources.
Include all valuable content, remove only dead air, filler, and redundant sections.
Order segments to create a logical cooking narrative: prep -> cook -> plate -> serve."""

    return f"""Analyze these cooking video transcripts and select the best segments to create
a cohesive {output_type} video.

{segments_text}

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
- Segments should be ordered to create a logical cooking flow
- Avoid including redundant content (e.g., two intros, repeated steps)
- Each segment should start and end at natural speech boundaries
- Order field determines the final sequence (0 = first segment played)"""
