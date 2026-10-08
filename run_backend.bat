@echo off
set PYTHONPATH=backend
uvicorn app.main:app --app-dir backend --reload
