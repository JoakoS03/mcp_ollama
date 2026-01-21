FROM python:3.13

ENV UV_VENV_DISABLED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv pip install --system .

RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-spa && \
    apt-get install -y --no-install-recommends poppler-utils &&\
    rm -rf /var/lib/apt/lists/*

COPY . .


