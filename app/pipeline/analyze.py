import json
import re
import time

import anthropic

from app.models.schemas import EditPlan, StitchPlan, Transcript
from app.prompts import cut_to_short, edit_longform, stitch


def _call_claude(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Send a prompt to Claude and return the text response."""
    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except anthropic.APIError as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
            continue

    raise RuntimeError("Failed to get response from Claude after 3 attempts")


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from Claude's response, handling text preamble."""
    text = text.strip()

    # Try extracting from markdown code block first
    code_block = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if code_block:
        return json.loads(code_block.group(1))

    # Try finding the first { ... } JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"No JSON found in Claude response:\n{text[:500]}")


def analyze_for_short(
    transcript: Transcript,
    source_file: str,
    api_key: str,
    min_duration: int = 30,
    max_duration: int = 60,
) -> EditPlan:
    """Analyze transcript and get Claude's edit plan for a short."""
    prompt = cut_to_short.build_prompt(transcript, min_duration, max_duration)
    response = _call_claude(cut_to_short.SYSTEM_PROMPT, prompt, api_key)
    data = _parse_json(response)

    data["source_file"] = source_file
    data["task_type"] = "cut_to_short"

    return EditPlan.model_validate(data)


def analyze_for_stitch(
    transcripts: list[Transcript],
    source_files: list[str],
    api_key: str,
    output_type: str = "longform",
    min_short: int = 30,
    max_short: int = 60,
) -> StitchPlan:
    """Analyze multiple transcripts and get Claude's stitch plan."""
    prompt = stitch.build_prompt(transcripts, output_type, min_short, max_short)
    response = _call_claude(stitch.SYSTEM_PROMPT, prompt, api_key)
    data = _parse_json(response)

    data["source_files"] = source_files

    return StitchPlan.model_validate(data)


def analyze_for_longform(
    transcript: Transcript,
    source_file: str,
    api_key: str,
) -> EditPlan:
    """Analyze transcript and get Claude's edit plan for longform cleanup."""
    prompt = edit_longform.build_prompt(transcript)
    response = _call_claude(edit_longform.SYSTEM_PROMPT, prompt, api_key)
    data = _parse_json(response)

    data["source_file"] = source_file
    data["task_type"] = "edit_longform"

    return EditPlan.model_validate(data)
