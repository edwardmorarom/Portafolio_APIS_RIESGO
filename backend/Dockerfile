FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV DEBUG=false
ENV DATABASE_URL=sqlite:///./data/portafolio_riesgo.db

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY roboadvisor_cache.csv /app/roboadvisor_cache.csv

WORKDIR /app/backend

RUN python -m app.db.seed_db \
    && python -m app.db.import_perri_prices

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
