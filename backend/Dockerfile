FROM python:3.12.13-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b

ARG PIP_VERSION=25.1.1

WORKDIR /app

COPY requirements.txt requirements.lock.txt ./

# O lock contém dependências diretas e transitivas com hashes. A versão do
# instalador também é fixa para evitar diferenças de resolução entre builds.
RUN python -m pip install --no-cache-dir "pip==${PIP_VERSION}" && \
    python -m pip install --no-cache-dir --require-hashes -r requirements.lock.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "entrypoint.sh"]

# CMD padrão de fallback (o docker-compose.yml sobrescreve isso com --reload em dev).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
