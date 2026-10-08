# TVN Media Copilot — Starter del MVP

Starter para la **Fase 1: Media** del reto “De la señal a la decisión”.

## Alcance de este incremento

Este primer bloque implementa únicamente:

1. carga de `noticias.csv` e `indicadores.csv`;
2. validación de columnas mínimas;
3. validación de IDs, URLs y fechas;
4. reporte de nulos sin rellenarlos con cero;
5. detección de IDs/registros duplicados;
6. separación lógica de filas con incidencias sin detener toda la carga;
7. generación de un reporte de calidad en JSON y Markdown;
8. copia validada de los datasets con columnas de diagnóstico.

Aún **no** implementa clasificación, agrupación semántica, ranking, generación con IA,
fichas editoriales ni interfaz final. Esas piezas aparecen reservadas en `src/tvn_copilot/services/`
para los siguientes incrementos.

## Requisito documental cubierto

Corresponde a la etapa **1 · Cargar**: leer el paquete público congelado, validar IDs, URLs,
fechas, campos obligatorios y filas nulas, y emitir un reporte de calidad.

También prepara T01: un archivo con fechas inválidas y nulos debe ser procesado sin bloquear
toda la carga.

## Python

Se propone Python 3.12 para reducir riesgo de incompatibilidades durante el hackathon.

## Instalación

### Windows / PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Ejecutar la validación de ejemplo

```powershell
python scripts\validate_snapshot.py
```

También puedes ejecutar:

```powershell
.\run_validate.bat
```

La ejecución usa por defecto `data/sample/`, que contiene datos sintéticos preparados para
probar errores de fecha, nulos y duplicados.

## Usar el snapshot real

Coloca los archivos en:

```text
data/snapshot/noticias.csv
data/snapshot/indicadores.csv
```

Luego cambia `.env`:

```env
NEWS_CSV=data/snapshot/noticias.csv
INDICATORS_CSV=data/snapshot/indicadores.csv
```

o ejecuta:

```powershell
python scripts\validate_snapshot.py `
  --news data\snapshot\noticias.csv `
  --indicators data\snapshot\indicadores.csv
```

## Salidas

Se generan:

```text
reports/data_quality/data_quality_report.json
reports/data_quality/data_quality_report.md
data/processed/noticias_validated.csv
data/processed/indicadores_validated.csv
```

Las copias procesadas conservan todas las filas originales y añaden:

- `_validation_status`
- `_validation_errors`

No se rellena ningún dato ausente con cero.

## Pruebas

```powershell
pytest -q
```

## Documentación temporal mientras Notion está bloqueado

Trabajar en:

```text
docs/notion_temp/
```

Estas páginas reflejan la estructura obligatoria del espacio final de Notion. Cuando el host
habilite el workspace, su contenido se migra sin detener el desarrollo.

## Siguiente incremento

Clasificación temática + baseline simple para comenzar la etapa **2 · Organizar**.


## Bloque 2 · Clasificación temática baseline

Este incremento añade la etapa inicial de **Organizar**:

- seis categorías oficiales;
- baseline reproducible por reglas/palabras clave;
- abstención si no hay señal suficiente;
- abstención ante empate;
- `tema` original nunca se sobrescribe;
- predicción en `tema_baseline`;
- reporte de distribución y métricas de desarrollo;
- pruebas automatizadas.

El baseline **NO es IA**. Su función es servir de referencia para comparar después contra una
capacidad NLP/ML, como exige el reto.

### Ejecutar Bloque 1 + Bloque 2

```powershell
.\run_block2.bat
```

o manualmente:

```powershell
python scripts\validate_snapshot.py
python scripts\classify_baseline.py
```

Salida principal:

```text
data/processed/noticias_classified_baseline.csv
reports/baseline/baseline_classification_report.md
reports/baseline/baseline_classification_report.json
```

Columnas añadidas:

```text
tema_baseline
baseline_estado
baseline_coincidencias
baseline_keywords
baseline_empates
```

`sin_clasificar` es un estado técnico, no una séptima categoría del reto.

### Pruebas

```powershell
pytest -q
```

### Siguiente incremento

Agrupación de titulares del mismo evento + baseline de similitud, preparando T02 y la
comparación con embeddings semánticos.


## Bloque 3 · Agrupación baseline + preparación semántica

### Agrupación baseline

```powershell
python scripts\group_baseline.py
```

o ejecutar los tres bloques:

```powershell
.\run_block3.bat
```

Salidas:

```text
data/processed/noticias_grouped_baseline.csv
data/processed/grouping_pairs_baseline.csv
data/processed/grouping_clusters_baseline.csv
reports/grouping/grouping_baseline_report.md
reports/grouping/grouping_baseline_report.json
```

Método propuesto:
- TF-IDF de caracteres sobre `titulo`;
- similitud coseno;
- ventana temporal inicial de 3 días;
- compatibilidad temática cuando existe;
- componentes conectados.

Los umbrales son parámetros del equipo y deben calibrarse contra etiquetas humanas.

### Preparar embeddings semánticos

Esta parte queda preparada, pero separada del MVP base para no añadir una dependencia pesada
a la instalación principal.

Instalar opcionalmente:

```powershell
pip install -r requirements-semantic.txt
```

Preparar artefacto:

```powershell
python scripts\prepare_embeddings.py
```

Salida:

```text
data/embeddings/news_embeddings.npz
data/embeddings/news_embeddings.meta.json
```

La propuesta usa por defecto un modelo multilingüe de Sentence Transformers. El nombre del
modelo es una decisión técnica del equipo, no un requisito del documento, y puede cambiarse.

Los embeddings se congelan para que la demo posterior no dependa de una llamada en vivo.

### T02

Se añadió un fixture sintético y una prueba automática que verifica que tres titulares del
mismo evento se agrupan sin convertir tres registros en tres procedencias independientes.

El fixture solo valida comportamiento técnico; la calidad real debe medirse contra
`cluster_humano`.


## Bloque 4 · Clustering semántico + evaluación contra `cluster_humano`

### 1. Generar embeddings reales

```powershell
pip install -r requirements-semantic.txt
python scripts\prepare_embeddings.py
```

### 2. Ejecutar clustering semántico

```powershell
python scripts\cluster_semantic.py
```

Salidas:

```text
data/processed/noticias_grouped_semantic.csv
data/processed/grouping_pairs_semantic.csv
reports/semantic_grouping/semantic_grouping_report.md
```

Parámetros iniciales propuestos:

```text
similarity_threshold = 0.78
max_days_apart = 3
```

Estos valores deben calibrarse con etiquetas humanas.

### 3. Crear plantilla de etiquetado humano

```powershell
python scripts\create_human_labels_template.py
```

Genera:

```text
data/etiquetas_humanas.csv
```

La columna `cluster_humano` debe usar el mismo ID para todas las noticias que la persona
considere pertenecientes al mismo evento.

Ejemplo:

```text
N001 -> H001
N004 -> H001
N010 -> H002
```

No existe un tamaño fijo impuesto por este starter. El tamaño de muestra debe decidirse y
documentarse según el tiempo disponible y la calidad de evaluación buscada.

### 4. Evaluar baseline y semántico

```powershell
python scripts\evaluate_clustering.py
```

Salida:

```text
reports/evaluation/clustering_evaluation.md
reports/evaluation/clustering_evaluation.json
data/processed/clustering_evaluation_rows.csv
```

Métricas:

- precision par-a-par;
- recall par-a-par;
- F1 par-a-par;
- delta semántico vs baseline.

Las métricas finales solo deben reportarse si `cluster_humano` proviene de revisión humana.

### Prueba controlada incluida

`data/sample/semantic_fixture.csv` y `data/sample/semantic_labels_fixture.csv` existen solo para
verificar el código. No representan resultados del proyecto.


## v0.5 · Arquitectura profesional + contextualización + Evidence Engine + R/I/U/N/E

- Ollama/Qwen eliminado del MVP.
- Gemini es el único LLM habilitado, detrás de `LLMProvider`.
- FastAPI + Next.js + DuckDB + Docker Compose + GitHub Actions.
- Contextualización conservadora con Banco Mundial.
- `EvidencePackage` trazable antes de cualquier generación.
- Priorización con `P = 30R + 25I + 20U + 15N + 10E`.
- Las reglas que convierten señales a R/I/U/N/E son propuesta `attention-v0.1-proposed`, no reglas dadas por el reto.
- `/generate/{cluster_id}` se abstiene si evidencia es insuficiente.

### Ejecutar backend
```powershell
pip install -r backend/requirements.txt
$env:PYTHONPATH="backend"
python backend/bootstrap_db.py
uvicorn app.main:app --app-dir backend --reload
```
OpenAPI: `http://localhost:8000/docs`

### Endpoints
`GET /health` · `GET /news` · `GET /topics/{cluster_id}/analysis` · `POST /ranking/score` · `POST /generate/{cluster_id}`

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

### Docker
```powershell
Copy-Item .env.example .env
docker compose up --build
```

### Agenda priorizada
`GET /agenda?limit=5` ordena por score; en empate aplica mayor urgencia y luego ID, y devuelve score desglosado, explicaciones y estado de evidencia.


## v0.6 · Ingesta real

Se añadió la primera etapa del pipeline productivo:

```text
TVN RSS + GDELT + World Bank
          ↓
raw/
          ↓
normalización
          ↓
deduplicación
          ↓
snapshot CSV + Parquet
          ↓
manifest + hashes
```

Ejecutar:

```powershell
Copy-Item .env.example .env
pip install -r backend/requirements.txt
$env:PYTHONPATH="backend"
python scripts/ingest_real_data.py
```

Salida:

```text
data/snapshot/noticias.csv
data/snapshot/noticias.parquet
data/snapshot/indicadores.csv
data/snapshot/indicadores.parquet
data/snapshot/fuentes.json
data/snapshot/manifest.json
```

El período de noticias configurado es `2025-10-02` a `2026-09-30`, de acuerdo con la
aclaración posterior del host.

La implementación no promete cobertura completa si las fuentes públicas no conservan el
histórico. Toda cobertura efectiva y advertencia queda en el manifest.


## v0.6.1 · Calidad de datos: warning ≠ error

Se corrigió la validación para no tratar como corrupta una noticia GDELT únicamente porque
`fecha_publicacion` sea desconocida.

Estados:
- `ok`: registro completo según las reglas actuales.
- `warning`: utilizable, pero con una limitación documentada.
- `error`: requiere revisión antes de usarse.

Regla importante:
- TVN RSS sin `fecha_publicacion` → error.
- Otra fuente sin `fecha_publicacion`, pero con `fecha_deteccion` válida → warning.
- `fecha_deteccion` nunca se copia a `fecha_publicacion`.

El backend acepta `ok` y `warning` como filas utilizables. La urgencia puede usar detección como
fallback operativo de recencia, manteniendo ambas fechas separadas.

Diagnóstico:

```powershell
python scripts\inspect_data_quality.py
```


## v0.6.2 · Pipeline real y corrección temporal

Los 1,678 registros GDELT con `fecha_publicacion` desconocida son utilizables porque conservan
`fecha_deteccion`.

Se corrigieron los dos motores de clustering para que la ventana temporal use:

```text
fecha_publicacion
    ↓ si no existe
fecha_deteccion (solo como fallback operativo)
```

La fecha original nunca se reescribe.

También se evita guardar pares que están fuera de la ventana temporal, reduciendo consumo de memoria
sobre corpus reales.

### Continuar sin volver a descargar

```powershell
$env:PYTHONPATH="$PWD\src;$PWD\backend"
python scripts\audit_real_corpus.py
python scripts\classify_baseline.py
python scripts\group_baseline.py
```

O:

```powershell
.\run_real_pipeline.bat
```

Ese `.bat` valida, audita, clasifica y agrupa el snapshot ya descargado. **No ejecuta la ingesta.**

Después:

```powershell
pip install -r requirements-semantic.txt
python scripts\prepare_embeddings.py
python scripts\cluster_semantic.py
```


## v0.6.3 · Reparación PyTorch/Windows para embeddings

Si `prepare_embeddings.py` falla con:

```text
WinError 1114
Error loading ... torch\lib\c10.dll
```

no es un error del dataset ni del modelo Sentence Transformers. Es un fallo al cargar
las bibliotecas nativas de PyTorch en Windows.

Para este MVP se recomienda **PyTorch CPU**, porque generar embeddings de ~1,700 titulares
no requiere CUDA y así evitamos dependencias de drivers/GPU en el entorno de preparación.

Con la venv activa:

```powershell
.\repair_semantic_windows_cpu.bat
```

Después:

```powershell
python scripts\diagnose_semantic_env.py
python scripts\prepare_embeddings.py
python scripts\cluster_semantic.py
```

La aplicación desplegada no necesita ejecutar Sentence Transformers si se incluyen en el
artefacto de despliegue los embeddings congelados generados durante la preparación.


## v0.6.4 · WinError 1114 después de una importación exitosa

Si `repair_semantic_windows_cpu.bat` termina con:

```text
torch: ...+cpu
sentence-transformers: OK
```

pero `prepare_embeddings.py` vuelve a mostrar WinError 1114, el problema puede depender del
**orden en que Windows carga las DLL**. En la v0.6.4 `torch` se precarga antes de
`pandas`/`numpy`.

Prueba:

```powershell
python scripts\diagnose_torch_import_order.py
python scripts\prepare_embeddings.py
```

No vuelvas a descargar las noticias ni ejecutes el scraping.


## v0.6.5 · Evaluación humana del clustering real

Después de generar `noticias_grouped_semantic.csv`, no se debe concluir que el modelo semántico
es mejor únicamente porque cree menos clusters.

Primero compara la estructura:

```powershell
python scripts\summarize_clustering_comparison.py
```

Luego genera una muestra de revisión humana:

```powershell
python scripts\create_human_labels_template.py
```

Por defecto crea **120 filas** priorizando desacuerdos entre baseline y semántico y reservando
una parte para controles. El valor 120 es una **propuesta operativa del equipo**, no un requisito
del documento.

Para usar otra cantidad:

```powershell
python scripts\create_human_labels_template.py --limit 80
```

Para todo el corpus:

```powershell
python scripts\create_human_labels_template.py --mode all --limit 0
```

Completa manualmente `cluster_humano`. Mismo ID significa **mismo evento**, no solamente mismo tema.
Luego:

```powershell
python scripts\evaluate_clustering.py
```

La evaluación usa decisiones par-a-par (mismo evento / evento distinto), por lo que los nombres
de los clusters humanos no tienen que coincidir con los IDs generados por el sistema.


## v0.7 · Clustering seleccionado + ampliación temática semántica

La evaluación humana del clustering debe congelarse antes de seguir al Evidence Engine:

```powershell
python scripts\finalize_clustering_selection.py
```

Luego se amplía la cobertura temática sin llamar a otro modelo. Se usan los embeddings
congelados y las noticias clasificadas por el baseline como semillas para construir centroides
de los seis temas:

```powershell
python scripts\classify_semantic.py
```

Salida:

```text
data/processed/noticias_ready.csv
```

Regla:
- si baseline ya clasificó una noticia, se conserva;
- si baseline se abstuvo, el centroide semántico puede completar el tema;
- si la similitud o el margen son insuficientes, el sistema sigue absteniéndose;
- los conflictos baseline/semántico se registran y no se resuelven silenciosamente.

Los umbrales `0.45` de similitud y `0.04` de margen son una propuesta inicial del equipo y
deben validarse si existe `tema_humano`.

Después:

```powershell
$env:PYTHONPATH="$PWD\backend"
python backend\bootstrap_db.py
uvicorn app.main:app --app-dir backend --reload
```

Y en otra consola:

```powershell
Invoke-RestMethod "http://localhost:8000/agenda?limit=5"
```


## v0.7.1 · Prioridad ≠ suficiencia de evidencia

La agenda conserva la fórmula oficial de atención:

```text
P = 30R + 25I + 20U + 15N + 10E
```

pero devuelve también `workflow`:

```json
{
  "state": "requiere evidencia",
  "draft_enabled": false,
  "publication_enabled": false
}
```

Un caso puede tener prioridad alta y evidencia parcial. Eso significa **investigar primero**,
no publicar ni generar automáticamente.

Además, la contextualización del Banco Mundial ahora mira señales del titular. Por ejemplo, un
caso sobre desempleo usa el indicador de desempleo en lugar de adjuntar automáticamente PIB,
inflación, desempleo y exportaciones.

La selección de indicadores sigue siendo contexto macro anual y nunca prueba causalidad.


## v0.7.2 · Diagnóstico robusto de Gemini

Un error HTTP de Gemini ya no se convierte en `500 Internal Server Error`.
El backend devuelve `502` con un detalle seguro y útil, por ejemplo:

```json
{
  "detail": {
    "message": "No fue posible generar el borrador con Gemini.",
    "provider_detail": "Gemini HTTP 429 (RESOURCE_EXHAUSTED): ..."
  }
}
```

La API key ahora se envía mediante `x-goog-api-key` y no como parámetro de URL.

Antes de probar `/generate`, puede validarse Gemini sin depender de DuckDB ni del Evidence Engine:

```powershell
python scripts\test_gemini_connection.py
```

Si el script devuelve `Gemini: OK`, entonces la conectividad, API key y modelo están
correctos y cualquier fallo restante pertenece al flujo editorial.


## v0.7.3 · Reintentos para Gemini 503/429

Si la prueba mínima devuelve HTTP 200 pero `/generate` recibe:

```text
503 UNAVAILABLE: This model is currently experiencing high demand
```

la clave, el modelo y la conectividad ya están validados. El problema es transitorio del proveedor.

La llamada editorial ahora reintenta únicamente errores transitorios:

```text
408
429
500–599
timeouts/conexión
```

con backoff exponencial y jitter. No se reintentan 400/403 ni otros errores de configuración.

Configuración:

```env
GEMINI_MAX_RETRIES=4
GEMINI_RETRY_BASE_SECONDS=1.0
```

Con los valores por defecto, los intervalos son aproximadamente 1, 2 y 4 segundos antes
de agotar cuatro intentos. `REQUEST_TIMEOUT_SECONDS` controla cada intento por separado.

No se implementó fallback automático a otro modelo: cambiar de modelo queda como una decisión
explícita para evitar resultados no reproducibles durante la evaluación.


## v0.8 · Salidas editoriales estructuradas + contradicciones + cache offline

La generación ya no se limita a texto libre. El endpoint:

```powershell
POST /generate/{case_id}?mode=brief
POST /generate/{case_id}?mode=script
POST /generate/{case_id}?mode=digital
```

devuelve un objeto estructurado validado por el backend.

### Brief
- título propuesto;
- interés público;
- resumen de máximo 250 palabras;
- claims separados en hecho/declaración/inferencia/hipótesis;
- exactamente 3 preguntas de investigación;
- evidence_id utilizados;
- verificaciones pendientes.

### Guion
- texto de locución;
- objetivo 45–60 s;
- duración estimada;
- claims trazables.

### Copy digital
- máximo 80 palabras;
- claims trazables.

El backend rechaza:
- evidence_id inventados;
- claims sin cita;
- brief >250 palabras;
- copy >80 palabras;
- JSON inválido después de una ronda de reparación.

### Contradicciones

El Evidence Engine marca **posibles contradicciones** mediante reglas transparentes.
Nunca decide cuál fuente es verdadera. La contradicción se entrega a Gemini y queda como
verificación pendiente.

### Demo offline

Cada salida validada se congela en:

```text
data/cache/generation/
```

El cache usa una huella del paquete de evidencia. Si Gemini queda temporalmente inaccesible,
el endpoint puede devolver exactamente el borrador previamente validado para ese mismo caso y
evidencia.

Para preparar el cache de las tres modalidades para los casos elegibles del Top 5:

```powershell
python scripts\prewarm_generation_cache.py
```

Esto requiere FastAPI ejecutándose y conectividad a Gemini solo durante el prewarm.


## v0.9 · Frontend editorial + revisión humana persistida

El MVP ya cuenta con una interfaz operativa para el flujo completo:

```text
Top 5 → detalle → score R/I/U/N/E → evidencia → contradicciones → borrador → revisión humana
```

Estados humanos persistidos en la base:
- `aprobado como borrador`;
- `en revisión`;
- `descartado`.

La aprobación queda bloqueada si la evidencia no es suficiente. La publicación automática permanece deshabilitada.

### Ejecutar frontend

```powershell
cd frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Abrir `http://localhost:3000`.
