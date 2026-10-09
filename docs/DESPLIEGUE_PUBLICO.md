# Despliegue público para la demo del jurado

El PDF del reto requiere un prototipo ejecutable, demo offline reproducible y enlaces desde Notion al repositorio y la solución. No obliga expresamente a que el demo sea público en Internet, pero habilitaremos dos servicios para facilitar evaluación.

## Arquitectura

- API FastAPI + datos locales en Render Docker (HTTPS).
- Frontend Next.js en Vercel (HTTPS).
- Notion: presentación, casos y pruebas, vinculación al frontend y GitHub.
- La demo offline del jurado sigue siendo ejecutable localmente. El despliegue web no reemplaza T10.

## Preparación antes de subir el código

Ejecutar en la raíz del repositorio:

```powershell
Test-Path data\processed\noticias_grouped_semantic.csv
Test-Path data\processed\indicadores_validated.csv
git ls-files data/processed/noticias_grouped_semantic.csv data/processed/indicadores_validated.csv
git status -sb
python -m pytest -q
cd frontend; npm run build; cd ..
```

Si la ruta semántica no existe, reconstruir desde los scripts documentados, SIN usar fixture sintético como sustituto. Si no está versionada, incluir **solo** noticias normalizadas con metadatos/URL bajo las condiciones del reto, no artículos completos sin permiso:

```powershell
git add -f data/processed/noticias_grouped_semantic.csv
git add -f data/processed/indicadores_validated.csv
```

Antes de hacer commit verificar que las dos tablas contienen los registros previstos y que no se incluyen datos sensibles. El arranque público aborta si una tabla tiene menos de 100 filas.

## 1. Render — backend

1. En https://dashboard.render.com, `New > Blueprint`, vincular el GitHub del proyecto y usar `render.yaml`; alternativamente crear un Web Service Docker apuntando a `backend/Dockerfile` con contexto raíz.
2. En la variable `CORS_ORIGINS`, indicar temporalmente un origen válido, por ejemplo `http://localhost:3000`, sin slash final. Cuando exista URL de Vercel, sustituir por `https://<tu-proyecto>.vercel.app` y guardar/redeploy.
3. **No configurar `GEMINI_API_KEY` para la demo pública**. El backend recuperará solo los borradores cacheados si el fingerprint coincide. El resto de casos deben abstenerse; no permitirá llamadas pagadas desde usuarios anónimos.
4. Esperar despliegue y comprobar:
   - `https://<servicio>.onrender.com/health`
   - `https://<servicio>.onrender.com/agenda?limit=5`
   - `https://<servicio>.onrender.com/explore?limit=5`
   Las primeras solicitudes en plan gratuito pueden tardar por reactivación del servicio.
5. Si el deploy falla con `DEPLOY ERROR`, falta un CSV real o está incompleto; no reemplazarlo por archivos sample.

## 2. Vercel — frontend

1. Abrir https://vercel.com/new, importar el mismo GitHub.
2. Configurar **Root Directory = `frontend`**, framework Next.js.
3. En **Environment Variables / Production**, agregar `NEXT_PUBLIC_API_URL` = `https://<servicio>.onrender.com` (sin slash al final).
4. Desplegar y abrir `https://<tu-proyecto>.vercel.app`.
5. De vuelta en Render, configurar `CORS_ORIGINS=https://<tu-proyecto>.vercel.app` y desplegar de nuevo.
6. Probar F12 > Network: `/agenda?limit=5` y `/explore?limit=5` deben responder 200 desde la API pública.

`NEXT_PUBLIC_API_URL` se fija en el build de Next.js. Al cambiarla hay que redeployar el frontend.

## 3. Condiciones de seguridad y límites

- Esta demo es pública y **NO tiene autenticación para revisiones**; el estado editorial puede ser alterado por otras personas y es temporal porque el plan gratuito tiene almacenamiento efímero. No usar como repositorio de producción ni como bitácora oficial. Registrar evidencias auténticas en Notion.
- El frontend público no incluye clave de Gemini. Los tres borradores cacheados deberían funcionar cuando el conjunto de evidencias tenga la misma huella; comprobarlo. No prometer que los demás eventos generan texto.
- El despliegue público no ejecuta ingesta en vivo ni requiere streaming. La revisión local integral se demuestra aparte con T10 sin conexión.
- Publicar solo metadatos y fuentes permitidas, no contenido completo restringido ni claves.
- Render Free puede suspender servicios o reiniciar el almacenamiento. Si falla la demo pública, el paquete offline debe permitir reproducirla localmente.

## 4. Enlaces en Notion

Actualizar la portada y la página de pitch con las URLs HTTPS reales de Vercel y Render y adjuntar capturas/salidas de pruebas. Solo publicar el Notion Site cuando se haya revisado que todas las subpáginas son aptas para acceso público.
