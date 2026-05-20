FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt ./
RUN pip install --no-cache-dir --default-timeout=120 -r requirements-docker.txt

COPY . .
RUN pip install --no-cache-dir --no-deps .
RUN chmod +x /app/docker/entrypoint.sh

CMD ["/app/docker/entrypoint.sh"]

