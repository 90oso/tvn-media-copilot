# Media Copilot — evolución de inteligencia de decisiones para Panacea

## Alcance implementado
- **Modo editorial preservado**: la agenda y revisión editorial siguen siendo el caso original.
- **Dos perfiles adicionales** en la aplicación Next.js real: empresa y consultoría.
- **API /explore?profile=editorial|business|research**: cada expediente incorpora `decision_support` con próximos pasos, opciones de verificación, vacíos y aprobación humana.
- **Corrección funcional**: las fechas vacías ya no se envían como `date_from=` / `date_to=` (FastAPI rechazaba fechas vacías).
- **Pruebas automatizadas** para garantizar revisión humana y no confundir prioridad editorial con riesgo económico.

## Límites explícitos
- No se ha incorporado todavía ingestión multi-fuente configurable, monitoreo programado, búsqueda híbrida en producción ni un agente planificador autónomo.
- Los perfiles nuevos utilizan el corpus existente; no equivalen a modelos de impacto logístico o financiero validados.
- Las opciones son pasos de investigación y verificación, no recomendaciones de inversión, operación o decisiones automáticas.
- Las demos estáticas de `docs/` no prueban la integración real. Esta evolución se encuentra en la aplicación Next.js y FastAPI.

## Validación de la siguiente etapa
1. Probar el flujo real Next.js ↔ FastAPI con snapshot local y medir disponibilidad.
2. Etiquetar al menos 30 casos de un sector con un experto independiente.
3. Medir precisión de recuperación, falsos positivos, calidad de fuentes, utilidad de los próximos pasos y tiempo ahorrado.
4. Implementar conectores de fuentes con términos de uso claros, y búsqueda semántica híbrida con métricas de recuperación.
5. Solo después anunciar capacidad comercial validada en ese sector.

## Presentación sugerida para Panacea
«Media Copilot transforma información pública en expedientes trazables y próximos pasos supervisados. Nació para apoyar decisiones editoriales; estamos validando su adaptación a inteligencia empresarial y análisis sectorial».

La rama `feat/decision-intelligence-panacea` es aislada; no modificar `main` hasta que las pruebas y una revisión humana estén completas.

## Iteración 2: investigación orquestada
- Endpoint real `POST /research/investigate` con objetivo, perfil, fechas y límite de expedientes.
- Flujo acotado de tres pasos: recuperación del corpus → inspección de evidencia → próximos pasos supervisados.
- Devuelve trazabilidad de pasos, expedientes, estado de abstención y limitaciones explícitas.
- Validaciones HTTP para fechas invertidas y objetivos fuera de límite.
- **No es todavía un agente planificador autónomo**: no elige nuevas fuentes ni realiza navegación externa.
