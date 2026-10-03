# sheetsage2-serverless

RunPod Serverless worker for [m-a-p/SheetSage2](https://huggingface.co/m-a-p/SheetSage2).

This service is intentionally separate from `yue2-serverless`: SheetSage2 and YuE2 use different Python/PyTorch dependency sets. The cover flow is:

```
source audio URL -> SheetSage2 -> melody-only ABC -> YuE2 (cot=melody) -> cover audio
```

## Default model

- SheetSage2: `m-a-p/SheetSage2`
- Revision: `398b22834dac7dd05e09b9c4e40a39fc479ec502`
- Parent MERT2 revision is pinned by SheetSage2's config
- Python 3.11
- FFmpeg 6.1+
- PyTorch 2.8.0 / CUDA 12.6

## Request

Use a directly downloadable HTTPS URL, ideally a presigned R2/S3 URL:

```json
{
  "source_audio_url": "https://example.com/source.mp3",
  "melody_only": true,
  "dtype": "bf16",
  "preset": "default"
}
```

Optional fields: `max_seconds`, `overlap_seconds`, and `lookahead_seconds`.

## Response

```json
{
  "job_id": "...",
  "status": "complete",
  "abc": "X:1\n...",
  "warnings": [],
  "artifacts": {}
}
```

The ABC is returned inline so an orchestrator can immediately call YuE2 with:

```json
{
  "style": "Thai alternative R&B, warm male vocal, 92 BPM",
  "lyrics": "...",
  "cot": "melody",
  "abc": "X:1\n..."
}
```

## RunPod CLI

```bash
runpodctl serverless run <endpoint-id> \
  --input '{"source_audio_url":"https://example.com/song.mp3","melody_only":true}' \
  --wait 20m
```

## Environment

| Variable | Default |
| --- | --- |
| `SHEETSAGE2_MODEL` | `m-a-p/SheetSage2` |
| `SHEETSAGE2_REVISION` | pinned commit above |
| `SHEETSAGE2_DEVICE` | `cuda` |
| `SHEETSAGE2_DTYPE` | `bf16` |
| `SHEETSAGE2_PRELOAD` | `true` |
| `SHEETSAGE2_LOCAL_FILES_ONLY` | `false` |
| `HF_HOME` | `/root/.cache/huggingface` |
| `SHEETSAGE2_MAX_AUDIO_BYTES` | `262144000` |
| `SHEETSAGE2_ALLOW_HTTP` | `false` |
| `S3_BUCKET` | empty |
| `S3_ENDPOINT_URL` | empty |
| `S3_REGION` | `auto` |
| `S3_PUBLIC_BASE_URL` | empty |

URLs resolving to loopback, private, link-local, reserved, multicast, or unspecified IP ranges are rejected. Redirects are revalidated.

## Artifacts

The main cover output is `abc` in the response. If S3-compatible storage is configured, generated score/MIDI/annotation files are uploaded and returned under `artifacts`.

## License

The wrapper code in this repository is separate from model weights. SheetSage2 and MERT-v2-FullSong currently declare CC BY-NC 4.0 model licenses. Review upstream terms before commercial deployment.
