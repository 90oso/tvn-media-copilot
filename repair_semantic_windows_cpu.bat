@echo off
setlocal

echo ==============================================
echo TVN Media Copilot - Reparar NLP semantico CPU
echo ==============================================

echo.
echo [1/5] Actualizando herramientas de pip...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error

echo.
echo [2/5] Quitando instalaciones PyTorch potencialmente incompatibles...
python -m pip uninstall -y torch torchvision torchaudio

echo.
echo [3/5] Instalando PyTorch CPU desde el indice oficial...
python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto :error

echo.
echo [4/5] Verificando Sentence Transformers...
python -m pip install --upgrade "sentence-transformers>=3.0,<4.0"
if errorlevel 1 goto :error

echo.
echo [5/5] Prueba de importacion...
python -c "import torch; print('torch:', torch.__version__); print('CUDA disponible:', torch.cuda.is_available()); from sentence_transformers import SentenceTransformer; print('sentence-transformers: OK')"
if errorlevel 1 goto :runtime

echo.
echo Reparacion completada.
echo Ahora ejecuta:
echo   python scripts\prepare_embeddings.py
exit /b 0

:runtime
echo.
echo ERROR: PyTorch sigue sin poder cargar sus DLL.
echo Instala o repara Microsoft Visual C++ Redistributable x64 y reinicia Windows.
echo Luego vuelve a ejecutar este archivo.
exit /b 2

:error
echo.
echo ERROR: fallo la instalacion.
exit /b 1
