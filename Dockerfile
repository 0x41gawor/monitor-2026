FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY readme.md ./

COPY app ./app
COPY infra ./infra
COPY monitor ./monitor
COPY job.py ./job.py

RUN pip install --no-cache-dir .

CMD ["python", "-m", "app.scheduler"]