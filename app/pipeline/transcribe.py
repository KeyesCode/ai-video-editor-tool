import whisper

from app.models.schemas import Transcript, TranscriptSegment

_model_cache: dict[str, whisper.Whisper] = {}


def _get_model(model_name: str) -> whisper.Whisper:
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def transcribe(audio_path: str, model_name: str = "base") -> Transcript:
    """Transcribe audio file using Whisper, returning structured transcript."""
    model = _get_model(model_name)
    result = model.transcribe(audio_path, word_timestamps=True)

    segments = []
    for seg in result.get("segments", []):
        segments.append(
            TranscriptSegment(
                start=round(seg["start"], 2),
                end=round(seg["end"], 2),
                text=seg["text"].strip(),
            )
        )

    full_text = " ".join(s.text for s in segments)
    duration = segments[-1].end if segments else 0.0

    return Transcript(
        segments=segments,
        full_text=full_text,
        duration=duration,
    )
