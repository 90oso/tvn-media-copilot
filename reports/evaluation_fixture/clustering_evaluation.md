# Evaluación de agrupación contra `cluster_humano`

- Noticias con etiqueta humana: **4**

## Métrica

Se evalúan pares de noticias: `mismo evento` vs `evento distinto`. Esto evita exigir que el sistema y el etiquetador utilicen el mismo nombre de cluster.

| Método | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 1.0000 | 0.3333 | 0.5000 | 1 | 0 | 2 |
| Semántico | 1.0000 | 1.0000 | 1.0000 | 3 | 0 | 0 |

## Cambio semántico vs baseline

- Δ precision: **+0.0000**
- Δ recall: **+0.6667**
- Δ F1: **+0.5000**

> Solo presentar estas cifras como evaluación real si `cluster_humano` fue construido mediante revisión humana.