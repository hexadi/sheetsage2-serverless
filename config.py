from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("SHEETSAGE2_MODEL", "m-a-p/SheetSage2")
    revision: str = os.getenv(
        "SHEETSAGE2_REVISION",
        "398b22834dac7dd05e09b9c4e40a39fc479ec502",
    )
    device: str = os.getenv("SHEETSAGE2_DEVICE", "cuda")
    dtype: str = os.getenv("SHEETSAGE2_DTYPE", "bf16")
    preload: bool = _bool("SHEETSAGE2_PRELOAD", True)
    local_files_only: bool = _bool("SHEETSAGE2_LOCAL_FILES_ONLY", False)
    hf_token: str | None = os.getenv("HF_TOKEN") or None
    hf_cache_dir: str = os.getenv("HF_HOME", "/root/.cache/huggingface")
    output_dir: str = os.getenv("SHEETSAGE2_OUTPUT_DIR", "/tmp/sheetsage2-output")
    keep_job_dir: bool = _bool("SHEETSAGE2_KEEP_JOB_DIR", False)

    max_audio_bytes: int = int(os.getenv("SHEETSAGE2_MAX_AUDIO_BYTES", str(250 * 1024 * 1024)))
    allow_http: bool = _bool("SHEETSAGE2_ALLOW_HTTP", False)
    connect_timeout: float = float(os.getenv("SHEETSAGE2_CONNECT_TIMEOUT", "10"))
    read_timeout: float = float(os.getenv("SHEETSAGE2_READ_TIMEOUT", "120"))

    s3_bucket: str | None = os.getenv("S3_BUCKET") or None
    s3_endpoint_url: str | None = os.getenv("S3_ENDPOINT_URL") or None
    s3_region: str = os.getenv("S3_REGION", "auto")
    s3_access_key_id: str | None = os.getenv("S3_ACCESS_KEY_ID") or None
    s3_secret_access_key: str | None = os.getenv("S3_SECRET_ACCESS_KEY") or None
    s3_public_base_url: str | None = os.getenv("S3_PUBLIC_BASE_URL") or None
    s3_prefix: str = os.getenv("S3_PREFIX", "sheetsage2/jobs").strip("/")
    s3_url_ttl_seconds: int = int(os.getenv("S3_URL_TTL_SECONDS", "86400"))

    def prepare(self) -> None:
        Path(self.hf_cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
