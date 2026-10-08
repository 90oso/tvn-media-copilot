# Reporte baseline de agrupación

- Versión: `tfidf-char-cosine-v0.1`
- Filas: **1728**
- Clusters totales: **1370**
- Clusters con 2+ noticias: **134**
- Umbral: **0.42**
- Ventana temporal: **3 días**

## Método

- TF-IDF de caracteres 3-5 sobre titular.
- Similitud coseno.
- Filtro temporal usando publicación; detección solo como fallback operativo.
- Compatibilidad temática cuando existe.
- Componentes conectados para formar clusters.

## Interpretación

El cluster indica **posible pertenencia al mismo evento**, no veracidad ni corroboración independiente.

La cantidad de procedencias independientes se registra por separado para no convertir múltiples reproducciones de una misma procedencia en evidencia adicional.

## Próximo paso

Comparar este baseline con agrupación por embeddings semánticos sobre una muestra etiquetada por humanos.