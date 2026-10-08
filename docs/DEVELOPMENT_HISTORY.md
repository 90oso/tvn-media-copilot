# Historial de desarrollo — TVN Media Copilot

## Propósito

Este documento conserva la cronología técnica real del proyecto. Las etapas v0.1–v0.9.1 fueron reconstruidas desde artefactos, scripts, reportes y resultados de ejecución. **No se han creado commits retroactivos ni se pretende simular una historia de Git inexistente.**

## Flujo construido

```text
Fuentes públicas
→ ingesta
→ validación y normalización
→ snapshot
→ clasificación y clustering
→ ranking
→ evidencia
→ generación con Gemini
→ revisión humana
```

La publicación automática está fuera del flujo.

## Cronología

### v0.1–v0.2 — Starter y baseline
Se creó la estructura inicial y un baseline interpretable de clasificación en seis temas: economía, logística/Canal, turismo, servicios públicos, eventos naturales y regulación.

Sobre el corpus real posterior, el baseline clasificó 241 de 1,728 noticias; 1,487 quedaron sin clasificación clara o en empate. Esto motivó una capa semántica posterior.

### v0.3–v0.4 — Agrupación baseline y semántica
Se implementó agrupación TF-IDF y luego embeddings con:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

El objetivo fue comparar un método sencillo con uno semántico y conservar ambos para evaluación.

### v0.5 — Arquitectura de MVP
El proyecto pasó de scripts aislados a una estructura de producto:
- FastAPI.
- Next.js/React.
- DuckDB.
- Docker.
- Servicios separados para ingestión, NLP/ML, evidencia, ranking, generación y revisión.

### v0.6 — Ingesta pública real
Fuentes:
- TVN RSS.
- GDELT DOC 2.0.
- World Bank API.

Ventana de noticias:
`2025-10-02` a `2026-09-30`.

Resultado:
- 1,728 noticias.
- 540 observaciones de indicadores.

La configuración explícita es 6 países × 6 indicadores × 15 años = 540. Cualquier cifra distinta presente en documentación externa debe registrarse como discrepancia, no corregirse silenciosamente.

### v0.6.1–v0.6.2 — Calidad y fecha efectiva
Se detectó que numerosos registros GDELT carecían de `fecha_publicacion`.

Resultado:
- 50 OK.
- 1,678 warnings.
- 0 errores.
- 1,728 utilizables.

Decisión:
- usar `fecha_publicacion` si existe;
- usar `fecha_deteccion` como fallback;
- conservar las columnas originales y el warning.

Resultados de agrupación:
- Baseline: 1,370 clusters; 134 con 2+ noticias.
- Semántico: 1,291 clusters; 148 con 2+ noticias.

### v0.6.3–v0.6.4 — Incidente PyTorch/Windows
Problema observado:
`WinError 1114` al cargar `c10.dll`.

Diagnóstico:
el orden de importación afectaba la carga de PyTorch.

Corrección:
precargar `torch` antes de ciertas librerías de datos.

Resultado:
- 1,728 embeddings.
- 384 dimensiones.

### v0.6.5–v0.7 — Evaluación humana y selección
Se preparó etiquetado humano donde noticias del mismo evento concreto comparten `cluster_humano`.

Evaluación sobre 120 etiquetas válidas:

| Método | Precision | Recall | F1 |
|---|---:|---:|---:|
| Baseline | 0.9444 | 0.8947 | 0.9189 |
| Semántico | 1.0000 | 0.8947 | 0.9444 |

Se seleccionó clustering semántico para el MVP, limitado a la evidencia disponible en esa muestra.

### v0.7.1 — Ranking y evidencia
Se mantuvo la fórmula:

`P = 30R + 25I + 20U + 15N + 10E`

Bandas:
- baja: [0,40)
- media: [40,70)
- alta: [70,100]

La prioridad se mantiene separada del estado de evidencia. Un evento de prioridad alta puede seguir requiriendo investigación.

### v0.7.2–v0.7.3 — Gemini
Se consolidó Gemini como LLM del MVP.

Modelo probado exitosamente:
`gemini-3.6-flash`

Se añadieron diagnósticos y retry exponencial con jitter para errores transitorios. No se implementó fallback silencioso a otro modelo.

### v0.8 — Generación editorial
Salidas:
- brief ≤250 palabras;
- 3 preguntas;
- título e interés público;
- fuentes y pendientes;
- guion 45–60 s;
- copy digital ≤80 palabras.

Se añadieron controles de evidencia, citas, contradicciones y cache reproducible.

### v0.9 — Interfaz editorial
El frontend incorporó agenda, detalle del evento, score, evidencia, generación y revisión humana.

### v0.9.1 — Optimización
`prewarm_generation_cache.py` agotaba el timeout al consultar `/agenda`.

Causa:
patrón N+1.

Corrección:
carga masiva de noticias, indicadores y revisiones, seguida de agrupación y análisis en memoria.

Validación registrada:
**44 pruebas superadas**.

## Incidentes que deben conservarse como evidencia

1. **GDELT sin `fecha_publicacion`** → fallback controlado a `fecha_deteccion`.
2. **PyTorch `WinError 1114`** → corrección de orden de imports.
3. **Gemini 503** → retry exponencial.
4. **Agenda lenta** → eliminación de N+1.
5. **Evidencia insuficiente** → abstención/HTTP 422 en lugar de generación no respaldada.

## Regla desde Git

Desde el primer commit real:
- todos los cambios funcionales van a Git;
- las decisiones relevantes se registran en `DECISIONS.md`;
- las métricas se respaldan con archivos en `reports/`;
- los secretos y artefactos locales regenerables permanecen fuera del repositorio.
