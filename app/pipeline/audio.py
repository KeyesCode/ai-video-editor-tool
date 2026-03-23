import subprocess
import tempfile
from pathlib import Path


def extract_audio(video_path: str, output_path: str | None = None) -> str:
    """Extract audio from video as 16kHz mono WAV for Whisper."""
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path,
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    return output_path
