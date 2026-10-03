FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:/root/.local/bin:$PATH" \
    HF_HOME=/root/.cache/huggingface \
    SHEETSAGE2_OUTPUT_DIR=/tmp/sheetsage2-output

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    git \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv python install 3.11 \
    && uv venv --python 3.11 "$VIRTUAL_ENV"

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip wheel \
    && python -m pip install torch==2.8.0 torchaudio==2.8.0 \
       --index-url https://download.pytorch.org/whl/cu126 \
    && python -m pip install -r requirements.txt

COPY config.py download.py engine.py storage.py handler.py ./

CMD ["python", "-u", "handler.py"]
