# Evaluación de agrupación contra `cluster_humano`

- Noticias con etiqueta humana: **120**

## Métrica

Se evalúan pares de noticias: `mismo evento` vs `evento distinto`. Esto evita exigir que el sistema y el etiquetador utilicen el mismo nombre de cluster.

| Método | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 0.9444 | 0.8947 | 0.9189 | 17 | 1 | 2 |
| Semántico | 1.0000 | 0.8947 | 0.9444 | 17 | 0 | 2 |

## Cambio semántico vs baseline

- Δ precision: **+0.0556**
- Δ recall: **+0.0000**
- Δ F1: **+0.0255**

> Solo presentar estas cifras como evaluación real si `cluster_humano` fue construido mediante revisión humana.