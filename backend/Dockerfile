FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "entrypoint.sh"]

# CMD padrão de fallback (o docker-compose.yml sobrescreve isso com --reload em dev).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]