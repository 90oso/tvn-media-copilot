# Reporte de agrupación semántica

- Noticias: **1728**
- Clusters: **1291**
- Clusters con 2+ noticias: **148**
- Umbral coseno: **0.78**
- Ventana temporal: **3 días**

## Interpretación

Cada cluster representa una hipótesis de que varias noticias se refieren al mismo evento. No implica veracidad ni corroboración independiente.

## Validación pendiente

El umbral debe compararse contra `cluster_humano` y reportar precision, recall y F1 par-a-par.