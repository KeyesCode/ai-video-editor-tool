# CookVid

AI-powered cooking video editor. Automatically cuts, stitches, and cleans up cooking videos using Claude AI — no manual editing required.

## Features

- **Cut to Short** — Takes a long-form cooking video and creates a 30-60 second short by identifying the most engaging segment
- **Stitch Videos** — Combines multiple cooking videos into a cohesive long-form video or short
- **Edit Long-form** — Cleans up a long-form video by removing dead air, filler words, bad takes, and off-topic tangents

## How It Works

```
Video → FFmpeg extracts audio → Whisper transcribes → Claude analyzes transcript → FFmpeg applies edits → Output
```

1. Audio is extracted from the video using FFmpeg
2. [Whisper](https://github.com/openai/whisper) transcribes the audio locally with timestamps
3. The transcript is sent to Claude, which returns a structured edit plan (what to keep, cut, and reorder)
4. MoviePy/FFmpeg executes the edits and produces the final video

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and available in PATH
- An [Anthropic API key](https://console.anthropic.com/)

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
winget install ffmpeg
```

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd video-editor-tool

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### CLI

```bash
# Cut a long video into a short
python -m app.cli cut-to-short cooking_video.mp4 -o short.mp4

# Stitch multiple videos into a long-form video
python -m app.cli stitch video1.mp4 video2.mp4 video3.mp4 -o combined.mp4

# Stitch multiple videos into a short
python -m app.cli stitch video1.mp4 video2.mp4 --type short -o highlight.mp4

# Clean up a long-form video
python -m app.cli edit-longform raw_footage.mp4 -o cleaned.mp4

# Use a different Whisper model for better accuracy
python -m app.cli cut-to-short video.mp4 --whisper-model medium
```

### Web UI

```bash
python -m app.cli serve
```

Open `http://127.0.0.1:8000` in your browser. Upload videos, choose an editing mode, and download the result.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | `./output/<name>_<type>.mp4` |
| `--whisper-model` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` | `base` |
| `--type` | Stitch output type: `short` or `longform` | `longform` |
| `--host` | Web server host | `127.0.0.1` |
| `--port` | Web server port | `8000` |

## Configuration

Environment variables (set in `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | *required* |
| `WHISPER_MODEL` | Default Whisper model size | `base` |
| `OUTPUT_DIR` | Directory for output files | `./output` |

## Project Structure

```
video-editor-tool/
├── config.py              # Settings via environment variables
├── app/
│   ├── cli.py             # Click CLI commands
│   ├── web.py             # FastAPI web interface
│   ├── models/
│   │   └── schemas.py     # Pydantic data models
│   ├── pipeline/
│   │   ├── audio.py       # FFmpeg audio extraction
│   │   ├── transcribe.py  # Whisper transcription
│   │   ├── analyze.py     # Claude API integration
│   │   ├── edit.py        # MoviePy video editing
│   │   └── runner.py      # Pipeline orchestrator
│   ├── prompts/
│   │   ├── cut_to_short.py
│   │   ├── stitch.py
│   │   └── edit_longform.py
│   └── templates/
│       └── index.html     # Web UI
├── requirements.txt
├── setup.py
└── .env.example
```

## License

MIT
