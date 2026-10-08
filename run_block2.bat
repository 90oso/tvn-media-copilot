@echo off
python scripts\validate_snapshot.py
if errorlevel 1 exit /b %errorlevel%
python scripts\classify_baseline.py
pause
