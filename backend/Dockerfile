FROM python:3.11.9-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

COPY backend/requirements.txt /build/requirements.txt

RUN python -m pip install --upgrade pip \
    && python -m pip wheel --no-cache-dir --wheel-dir /build/wheels -r /build/requirements.txt


FROM python:3.11.9-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV DEBUG=false
ENV DATABASE_URL=sqlite:///./data/portafolio_riesgo.db

WORKDIR /app

COPY --from=builder /build/wheels /wheels
COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r /app/backend/requirements.txt \
    && rm -rf /wheels

COPY backend /app/backend
COPY roboadvisor_cache.csv /app/roboadvisor_cache.csv

WORKDIR /app/backend

RUN python -m app.db.seed_db \
    && python -m app.db.import_perri_prices

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
