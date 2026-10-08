# Arquitectura — TVN Media Copilot

## Flujo general

```text
TVN RSS / GDELT / World Bank
            |
            v
         Ingesta
            |
            v
 Validación y normalización
            |
            v
 Snapshot + datos procesados
            |
            v
 Clasificación + clustering
            |
            v
      Ranking R/I/U/N/E
            |
            v
     Motor de evidencia
            |
      +-----+------+
      |            |
      v            v
 Interfaz        Gemini
      |            |
      +-----+------+
            v
   Borrador estructurado
            |
            v
      Revisión humana
```

No existe publicación automática.

## Stack

- Backend: **FastAPI**
- Frontend: **Next.js / React**
- Persistencia local: **DuckDB**
- NLP/ML: **Python + Sentence Transformers**
- LLM: **Gemini**
- Contenedores: **Docker / docker-compose**

## Datos

Noticias:
`id_noticia, titulo, url, medio, idioma, fecha_publicacion, fecha_deteccion, fecha_extraccion, tema, origen, alcance_texto`

Indicadores:
`pais_iso3, indicador_id, anio, valor, unidad, fuente_url, fecha_extraccion, licencia`

## NLP/ML

Baseline:
- clasificación interpretable;
- agrupación TF-IDF.

Modelo semántico:
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

El método semántico fue seleccionado para el MVP después de evaluación humana.

## Ranking

Fórmula:

`P = 30R + 25I + 20U + 15N + 10E`

Los pesos se mantienen fijos. Las reglas operacionales que calculan cada componente deben estar versionadas por separado.

## Evidencia

Estados:
- insuficiente;
- parcial;
- suficiente para el borrador.

Principio:
**prioridad alta no equivale a permiso de publicación**.

La evidencia debe existir antes de la generación.

## Generación

Proveedor:
`Gemini`

Modelo probado:
`gemini-3.6-flash`

Controles:
- salida estructurada;
- validación Pydantic;
- IDs de evidencia válidos;
- límites de longitud;
- distinción hecho/inferencia/hipótesis;
- retry para errores transitorios;
- revisión humana obligatoria.

## Salidas

Brief:
- máximo 250 palabras;
- título;
- interés público;
- 3 preguntas;
- fuentes;
- pendientes.

Guion:
- 45–60 segundos.

Copy digital:
- máximo 80 palabras.

## Offline

El cache operativo local no se versiona. Para la demo offline se pueden conservar artefactos congelados y validados, claramente identificados como cache y vinculados a la huella de la evidencia.

## Seguridad

- `.env` fuera de Git.
- `.env.example` sin secretos.
- Gemini únicamente desde backend.
- No exponer claves al frontend.
- No copiar secretos a logs ni documentación.
