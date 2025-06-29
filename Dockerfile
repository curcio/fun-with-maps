# Multi-stage build for Fun with Maps

# Stage 1: build frontend assets using Node
FROM node:18 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: runtime with Python
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt
COPY backend/ ./backend/
COPY fun_with_maps/ ./fun_with_maps/
COPY --from=frontend-build /app/frontend/build/ ./backend/static/
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
