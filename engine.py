from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from config import settings

_ALLOWED = {
    "source_audio_url",
    "melody_only",
    "dtype",
    "preset",
    "max_seconds",
    "overlap_seconds",
    "lookahead_seconds",
}


def validate_request(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")

    unknown = set(data) - _ALLOWED
    if unknown:
        raise ValueError(f"unsupported input fields: {sorted(unknown)}")

    url = data.get("source_audio_url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("source_audio_url is required")

    dtype = data.get("dtype", settings.dtype)
    if dtype not in {"bf16", "fp32"}:
        raise ValueError("dtype must be bf16 or fp32")

    preset = data.get("preset", "default")
    if preset not in {"default", "paper"}:
        raise ValueError("preset must be default or paper")

    clean = dict(data)
    clean.setdefault("melody_only", True)
    clean.setdefault("dtype", dtype)
    clean.setdefault("preset", preset)

    for field in ("max_seconds", "overlap_seconds", "lookahead_seconds"):
        value = clean.get(field)
        if value is not None:
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{field} must be a non-negative number")

    return clean


class SheetSage2Engine:
    def __init__(self) -> None:
        self._model = None
        self._device = None
        self._load_lock = threading.Lock()
        self._infer_lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return self._model

        with self._load_lock:
            if self._model is not None:
                return self._model

            import torch
            from transformers import AutoModel

            settings.prepare()
            torch.set_num_threads(min(4, torch.get_num_threads()))

            device = settings.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cuda" and not torch.cuda.is_available():
                raise RuntimeError("CUDA is required but is not available")
            if device == "cuda" and settings.dtype == "bf16" and not torch.cuda.is_bf16_supported():
                raise RuntimeError("selected GPU does not support BF16")

            model = AutoModel.from_pretrained(
                settings.model,
                revision=settings.revision,
                code_revision=settings.revision,
                trust_remote_code=True,
                local_files_only=settings.local_files_only,
                cache_dir=settings.hf_cache_dir,
                token=settings.hf_token,
            )
            self._model = model.eval().to(device)
            self._device = device

        return self._model

    def warmup(self) -> None:
        self._load()

    def transcribe(self, request: dict[str, Any], audio_path: Path, output_dir: Path) -> dict[str, Any]:
        data = validate_request(request)
        model = self._load()

        options: dict[str, Any] = {
            "melody_only": data["melody_only"],
            "dtype": data["dtype"],
            "preset": data["preset"],
        }
        if data.get("max_seconds") is not None:
            options["max_seconds"] = data["max_seconds"]
        if data.get("overlap_seconds") is not None:
            options["overlap_seconds"] = data["overlap_seconds"]
        if data.get("lookahead_seconds") is not None:
            options["lookahead_seconds"] = data["lookahead_seconds"]

        def progress(value):
            if isinstance(value, dict) and value.get("stage") == "encoding":
                print(
                    f"SheetSage2 window {value.get('window')}/{value.get('windows')}",
                    flush=True,
                )

        options["progress"] = progress
        output_dir.mkdir(parents=True, exist_ok=False)

        with self._infer_lock:
            result = model.transcribe(str(audio_path), output_dir=str(output_dir), **options)

        abc = result.get("abc")
        if data["melody_only"] and (result.get("abc_error") or not abc):
            reason = result.get("abc_error") or "no ABC score was produced"
            raise RuntimeError(f"melody-only ABC unavailable: {reason}")

        (output_dir / "serverless-request.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "abc": abc,
            "abc_error": result.get("abc_error"),
            "warnings": result.get("warnings") or [],
        }


engine = SheetSage2Engine()
