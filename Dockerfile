# -- Stage 1: Build frontend --
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# -- Stage 2: Production image --
FROM python:3.12-slim-bookworm
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Headless Chromium for getting past Barchart's WAF challenge (see services/barchart.py)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Playwright's bundled Node driver links against libatomic, which this slim
# arm64 base does not carry. It has to be present before `playwright install`
# runs, since --with-deps resolves the browser packages by running that driver.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/*
RUN python -m playwright install --with-deps --only-shell chromium \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist /app/static

ENV CURVE_STATIC_DIR=/app/static
ENV CURVE_DATA_DIR=/app/data/snapshots

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
