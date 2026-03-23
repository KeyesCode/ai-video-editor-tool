import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import settings
from app.pipeline.runner import PipelineRunner

console = Console()
runner = PipelineRunner(settings)


def _progress_callback(job):
    """Print status updates to console."""
    status_labels = {
        "extracting_audio": "Extracting audio...",
        "transcribing": "Transcribing with Whisper...",
        "analyzing": "AI analyzing transcript...",
        "editing": "Applying edits with FFmpeg...",
        "complete": "Done!",
        "failed": f"Failed: {job.error}",
    }
    label = status_labels.get(job.status, job.status)
    console.print(f"  [{job.progress:.0%}] {label}")


@click.group()
def cli():
    """AI-powered cooking video editor."""
    if not settings.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.[/red]")
        raise SystemExit(1)


@cli.command("cut-to-short")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output file path")
@click.option("--whisper-model", default=None, help="Whisper model size (tiny/base/small/medium/large)")
def cut_to_short(input_file, output, whisper_model):
    """Cut a long-form cooking video into a 30-60 second short."""
    if whisper_model:
        settings.whisper_model = whisper_model

    console.print(f"\n[bold]Cutting to short:[/bold] {input_file}\n")
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Processing...", total=None)
        result = runner.cut_to_short(input_file, output, _progress_callback)
        progress.update(task, description="Complete!")

    console.print(f"\n[green]Short saved to:[/green] {result}\n")


@cli.command("stitch")
@click.argument("input_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--type", "output_type", type=click.Choice(["short", "longform"]), default="longform", help="Output type")
@click.option("-o", "--output", default=None, help="Output file path")
@click.option("--whisper-model", default=None, help="Whisper model size")
def stitch_cmd(input_files, output_type, output, whisper_model):
    """Stitch multiple cooking videos into one video."""
    if len(input_files) < 2:
        console.print("[red]Error: Need at least 2 videos to stitch.[/red]")
        raise SystemExit(1)

    if whisper_model:
        settings.whisper_model = whisper_model

    console.print(f"\n[bold]Stitching {len(input_files)} videos into {output_type}:[/bold]\n")
    for f in input_files:
        console.print(f"  - {f}")
    console.print()

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Processing...", total=None)
        result = runner.stitch(list(input_files), output_type, output, _progress_callback)
        progress.update(task, description="Complete!")

    console.print(f"\n[green]Stitched video saved to:[/green] {result}\n")


@cli.command("edit-longform")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output file path")
@click.option("--whisper-model", default=None, help="Whisper model size")
def edit_longform(input_file, output, whisper_model):
    """Clean up a long-form cooking video (remove dead air, filler, etc.)."""
    if whisper_model:
        settings.whisper_model = whisper_model

    console.print(f"\n[bold]Editing long-form:[/bold] {input_file}\n")
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Processing...", total=None)
        result = runner.edit_longform(input_file, output, _progress_callback)
        progress.update(task, description="Complete!")

    console.print(f"\n[green]Edited video saved to:[/green] {result}\n")


@cli.command("serve")
@click.option("--host", default=None, help="Web server host")
@click.option("--port", default=None, type=int, help="Web server port")
def serve(host, port):
    """Start the web UI."""
    import uvicorn
    from app.web import app

    h = host or settings.web_host
    p = port or settings.web_port
    console.print(f"\n[bold]Starting web UI at http://{h}:{p}[/bold]\n")
    uvicorn.run(app, host=h, port=p)


if __name__ == "__main__":
    cli()
