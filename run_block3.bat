@echo off
python scripts\validate_snapshot.py
if errorlevel 1 exit /b %errorlevel%
python scripts\classify_baseline.py
if errorlevel 1 exit /b %errorlevel%
python scripts\group_baseline.py
pause
