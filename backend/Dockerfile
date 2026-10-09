FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/start_hosted.py ./start_hosted.py
COPY data ./data
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app APP_ENV=production
EXPOSE 10000
CMD ["python", "start_hosted.py"]
