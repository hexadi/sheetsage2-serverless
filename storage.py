from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import quote

from config import settings

_ALLOWED_SUFFIXES = {".abc", ".mid", ".json", ".lab"}


def _client():
    if not settings.s3_bucket:
        return None

    import boto3

    kwargs: dict[str, Any] = {
        "service_name": "s3",
        "region_name": settings.s3_region,
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    if settings.s3_access_key_id:
        kwargs["aws_access_key_id"] = settings.s3_access_key_id
    if settings.s3_secret_access_key:
        kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
    return boto3.client(**kwargs)


def publish_artifacts(directory: Path, job_id: str) -> dict[str, dict[str, Any]]:
    client = _client()
    if client is None:
        return {}

    published: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
            continue
        if path.name == "serverless-request.json":
            continue

        relative = path.relative_to(directory).as_posix()
        key = f"{settings.s3_prefix}/{job_id}/{relative}"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        client.upload_file(
            str(path),
            settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

        if settings.s3_public_base_url:
            url = f"{settings.s3_public_base_url.rstrip('/')}/{quote(key, safe='/')}"
        else:
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket, "Key": key},
                ExpiresIn=settings.s3_url_ttl_seconds,
            )

        published[relative] = {"key": key, "url": url}

    return published
