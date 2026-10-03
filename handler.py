from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import runpod

from config import settings
from download import download_audio
from engine import engine, validate_request
from storage import publish_artifacts


def handler(job: dict) -> dict:
    job_id = str(job.get("id") or uuid.uuid4())
    request = validate_request(job.get("input"))
    settings.prepare()

    job_dir = Path(settings.output_dir) / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    job_dir.mkdir(parents=True, exist_ok=False)

    try:
        audio_path = download_audio(request["source_audio_url"], job_dir)
        output_dir = job_dir / "transcription"
        result = engine.transcribe(request, audio_path, output_dir)
        artifacts = publish_artifacts(output_dir, job_id)

        return {
            "job_id": job_id,
            "status": "complete",
            "abc": result["abc"],
            "abc_error": result["abc_error"],
            "warnings": result["warnings"],
            "artifacts": artifacts,
        }
    finally:
        if not settings.keep_job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)


if __name__ == "__main__":
    if settings.preload:
        print("Preloading SheetSage2 before accepting jobs...", flush=True)
        engine.warmup()
        print("SheetSage2 preload complete.", flush=True)
    runpod.serverless.start({"handler": handler})
