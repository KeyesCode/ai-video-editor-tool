from app.models.schemas import Transcript

SYSTEM_PROMPT = """You are a professional cooking video editor specializing in creating viral short-form content.
Your job is to analyze a cooking video transcript and identify the single best 30-60 second segment
that would make the most engaging short.

You must return ONLY valid JSON matching the exact schema specified."""


def build_prompt(transcript: Transcript, min_duration: int = 30, max_duration: int = 60) -> str:
    segments_text = "\n".join(
        f"[{s.start:.1f}s - {s.end:.1f}s] {s.text}"
        for s in transcript.segments
    )

    return f"""Analyze this cooking video transcript (total duration: {transcript.duration:.1f}s) and select
the best continuous segment for a {min_duration}-{max_duration} second short-form video.

TRANSCRIPT:
{segments_text}

SELECTION CRITERIA (in priority order):
1. Strong hook in the first 3 seconds - something visually interesting or an engaging statement
2. Self-contained cooking step - viewers should see a complete action (e.g., full searing, plating, mixing)
3. Visual appeal cues - look for mentions of: plating, sizzling, flipping, pouring, garnishing, slicing, caramelizing
4. Clear narration - the speaker should be explaining what they're doing
5. Natural start and end points - don't cut mid-sentence

Return JSON in this exact format:
{{
    "decisions": [
        {{
            "action": "keep",
            "start": <start_seconds>,
            "end": <end_seconds>,
            "reason": "<why this segment was chosen>"
        }}
    ],
    "output_duration": <duration_of_kept_segment>
}}

RULES:
- Select exactly ONE continuous segment between {min_duration} and {max_duration} seconds
- Timestamps must align with transcript segment boundaries (snap to nearest segment start/end)
- The segment must tell a mini-story: setup -> action -> result
- output_duration must equal end - start of the kept segment"""
