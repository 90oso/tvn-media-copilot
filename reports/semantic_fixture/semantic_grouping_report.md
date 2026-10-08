# Reporte de agrupación semántica

- Noticias: **4**
- Clusters: **2**
- Clusters con 2+ noticias: **1**
- Umbral coseno: **0.95**
- Ventana temporal: **2 días**

## Interpretación

Cada cluster representa una hipótesis de que varias noticias se refieren al mismo evento. No implica veracidad ni corroboración independiente.

## Validación pendiente

El umbral debe compararse contra `cluster_humano` y reportar precision, recall y F1 par-a-par.