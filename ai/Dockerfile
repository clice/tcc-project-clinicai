FROM python:3.12.13-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b

ARG PIP_VERSION=25.1.1

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.lock.txt ./

# O lock contém dependências diretas e transitivas com hashes. A versão do
# instalador também é fixa para evitar diferenças de resolução entre builds.
RUN python -m pip install --no-cache-dir "pip==${PIP_VERSION}" && \
    python -m pip install --no-cache-dir --require-hashes -r requirements.lock.txt

COPY app ./app
COPY training ./training

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
