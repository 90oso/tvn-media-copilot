# Changelog — TVN Media Copilot

> **Nota de trazabilidad:** las versiones v0.1–v0.9.1 se reconstruyeron a partir de artefactos versionados, scripts, reportes y resultados de ejecución. No representan commits históricos retroactivos.

## v0.9.1 — Optimización de agenda
- Se eliminó el patrón N+1 del endpoint de agenda.
- Se incorporaron cargas masivas de noticias, indicadores y revisiones.
- `prewarm_generation_cache.py` recibió timeouts más amplios y manejo limpio de errores.
- Validación registrada: **44 pruebas superadas**.

## v0.9 — Frontend y revisión humana
- Agenda priorizada.
- Vista de detalle del evento.
- Visualización de R/I/U/N/E y estado de evidencia.
- Generación editorial desde interfaz.
- Revisión humana persistida.
- Sin publicación automática.

## v0.8 — Salidas editoriales estructuradas
- Brief editorial de máximo 250 palabras.
- Guion de 45–60 s.
- Copy digital de máximo 80 palabras.
- Validación de IDs de evidencia y cobertura de citas.
- Detección transparente de posibles contradicciones.
- Cache reproducible para demo/offline.
- Validación registrada: **42 pruebas superadas**.

## v0.7.3 — Resiliencia Gemini
- Retry exponencial con jitter para 408, 429, 5xx, timeout y errores transitorios.
- Sin cambio automático de modelo.
- Generación exitosa observada con `gemini-3.6-flash`.

## v0.7.2 — Diagnóstico Gemini
- Errores más claros.
- Uso de `x-goog-api-key`.
- `scripts/test_gemini_connection.py`.
- Validación registrada: **35 pruebas superadas**.

## v0.7.1 — Ranking y evidencia
- Selección contextual de indicadores.
- Estado `parcial` → requiere evidencia.
- Estado `suficiente para el borrador` → habilita borrador sujeto a revisión.
- Publicación automática siempre deshabilitada.
- Validación registrada: **33 pruebas superadas**.

## v0.7 — Selección de clustering semántico
Evaluación humana sobre 120 etiquetas válidas:

| Método | Precision | Recall | F1 |
|---|---:|---:|---:|
| Baseline | 0.9444 | 0.8947 | 0.9189 |
| Semántico | 1.0000 | 0.8947 | 0.9444 |

Delta F1: **+0.0255**. Se seleccionó el método semántico para el MVP.

## v0.6.5 — Revisión humana
- Plantilla de etiquetado humano.
- Comparación baseline vs semántico.
- Reportes de evaluación.

## v0.6.4 — Compatibilidad PyTorch en Windows
- Corrección de `WinError 1114` / `c10.dll`.
- Precarga de `torch` antes de `pandas`/`numpy`.
- Embeddings generados: **1,728 noticias × 384 dimensiones**.

## v0.6.3 — Diagnóstico semántico
- Scripts de diagnóstico de PyTorch y orden de imports.

## v0.6.2 — Pipeline real
- Fecha efectiva: `fecha_publicacion`, con fallback a `fecha_deteccion`.
- Ventana temporal para pares semánticos.
- Baseline: 1,370 clusters; 134 con 2+ noticias.
- Semántico: 1,291 clusters; 148 con 2+ noticias.

## v0.6.1 — Validación de corpus
- 1,728 noticias cargadas.
- 50 OK.
- 1,678 warnings.
- 0 errores.
- 1,728 utilizables.

## v0.6 — Ingesta real
- TVN RSS.
- GDELT DOC 2.0.
- World Bank API.
- 1,728 noticias.
- 540 observaciones de indicadores.
- Ventana de noticias: 2025-10-02 a 2026-09-30.

## v0.5 — Arquitectura de producto
- FastAPI.
- Next.js/React.
- DuckDB.
- Docker.
- Separación entre ingestión, NLP/ML, ranking, evidencia, generación y revisión.

## v0.4 — Clustering semántico
- Embeddings multilingües.
- Infraestructura de evaluación.

## v0.3 — Baseline de agrupación
- TF-IDF.
- Pares candidatos.
- Comparación preparada contra método semántico.

## v0.2 — Baseline de clasificación
- Seis temas editoriales.
- Sobre el corpus real posterior: 241 clasificadas y 1,487 sin clasificación clara/empate.

## v0.1 — Starter
- Estructura inicial.
- Contratos de datos.
- Configuración.
- Primeros scripts y pruebas.

## Desde el primer commit real
A partir de aquí, toda nueva versión debe quedar respaldada por commits normales de Git y este changelog se actualizará únicamente con cambios reales.
