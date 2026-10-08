FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/bootstrap_db.py ./bootstrap_db.py
COPY data ./data
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
