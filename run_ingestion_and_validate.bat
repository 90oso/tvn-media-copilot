@echo off
set PYTHONPATH=backend
python scripts\ingest_real_data.py
if errorlevel 1 exit /b %errorlevel%
python scripts\validate_snapshot.py --news data\snapshot\noticias.csv --indicators data\snapshot\indicadores.csv
pause
