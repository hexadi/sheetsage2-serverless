from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from config import settings

_REDIRECTS = {301, 302, 303, 307, 308}
_AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".webm"}


def _check_host(hostname: str, port: int) -> None:
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"cannot resolve source host: {hostname}") from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("source_audio_url resolves to a non-public address")


def validate_source_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("source_audio_url must be a non-empty URL")

    parsed = urlparse(url)
    allowed = {"https"} | ({"http"} if settings.allow_http else set())
    if parsed.scheme.lower() not in allowed:
        raise ValueError("source_audio_url must use HTTPS")
    if not parsed.hostname:
        raise ValueError("source_audio_url must include a hostname")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    _check_host(parsed.hostname, port)
    return url


def _suffix(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in _AUDIO_SUFFIXES else ".bin"


def download_audio(url: str, directory: Path) -> Path:
    current = validate_source_url(url)
    directory.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    response = None
    for _ in range(6):
        response = session.get(
            current,
            stream=True,
            allow_redirects=False,
            timeout=(settings.connect_timeout, settings.read_timeout),
            headers={"User-Agent": "sheetsage2-serverless/0.1"},
        )
        if response.status_code in _REDIRECTS:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise ValueError("source redirect has no Location header")
            current = validate_source_url(urljoin(current, location))
            continue
        response.raise_for_status()
        break
    else:
        raise ValueError("too many source redirects")

    length = response.headers.get("Content-Length")
    if length and int(length) > settings.max_audio_bytes:
        response.close()
        raise ValueError("source audio exceeds configured size limit")

    target = directory / f"source{_suffix(current)}"
    written = 0
    try:
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                written += len(chunk)
                if written > settings.max_audio_bytes:
                    raise ValueError("source audio exceeds configured size limit")
                handle.write(chunk)
    finally:
        response.close()

    if written == 0:
        raise ValueError("source audio is empty")
    return target
