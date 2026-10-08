# Reporte baseline de agrupación

- Versión: `tfidf-char-cosine-v0.1`
- Filas: **4**
- Clusters totales: **2**
- Clusters con 2+ noticias: **1**
- Umbral: **0.35**
- Ventana temporal: **2 días**

## Método

- TF-IDF de caracteres 3-5 sobre titular.
- Similitud coseno.
- Filtro temporal.
- Compatibilidad temática cuando existe.
- Componentes conectados para formar clusters.

## Interpretación

El cluster indica **posible pertenencia al mismo evento**, no veracidad ni corroboración independiente.

La cantidad de procedencias independientes se registra por separado para no convertir múltiples reproducciones de una misma procedencia en evidencia adicional.

## Próximo paso

Comparar este baseline con agrupación por embeddings semánticos sobre una muestra etiquetada por humanos.