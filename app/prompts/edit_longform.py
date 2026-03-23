from app.models.schemas import Transcript

SYSTEM_PROMPT = """You are a professional cooking video editor. Your job is to clean up a long-form cooking
video by identifying segments to cut while preserving all valuable content. The result should be a
tighter, more engaging version of the same video that still feels long-form.

You must return ONLY valid JSON matching the exact schema specified."""


def build_prompt(transcript: Transcript) -> str:
    segments_text = "\n".join(
        f"[{s.start:.1f}s - {s.end:.1f}s] {s.text}"
        for s in transcript.segments
    )

    return f"""Analyze this cooking video transcript (total duration: {transcript.duration:.1f}s) and
identify segments to CUT to create a cleaner long-form video. Keep as much valuable content as possible.

TRANSCRIPT:
{segments_text}

WHAT TO CUT:
1. Dead air - pauses longer than 3 seconds with no speech or action description
2. Filler words/phrases - excessive "um", "uh", "you know", "like" sections
3. Repeated takes - if the same step is explained twice, keep the better take
4. Off-topic tangents - digressions unrelated to the cooking process
5. Technical difficulties - mentions of camera issues, audio problems, etc.
6. Unnecessary waiting - "now we wait for 10 minutes" type sections (unless they have useful tips)

WHAT TO KEEP:
1. All cooking instructions and techniques
2. Ingredient explanations and substitution tips
3. Personal stories that add character (keep brief ones)
4. Plating and final presentation
5. Taste testing and reactions

Return JSON in this exact format:
{{
    "decisions": [
        {{
            "action": "keep" or "cut",
            "start": <start_seconds>,
            "end": <end_seconds>,
            "reason": "<why keep or cut>"
        }}
    ],
    "output_duration": <total duration of all kept segments>
}}

RULES:
- Cover the ENTIRE video duration - every second must be in a "keep" or "cut" decision
- Decisions must be in chronological order with no gaps or overlaps
- Keep at least 70% of the original content (this is a cleanup, not a highlight reel)
- Timestamps must align with transcript segment boundaries
- The first decision should start at 0.0 and the last should end at {transcript.duration:.1f}
- output_duration must equal the sum of all "keep" segment durations"""
