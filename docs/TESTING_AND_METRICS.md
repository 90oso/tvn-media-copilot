# Pruebas y métricas — TVN Media Copilot

## Suite automatizada registrada

| Versión | Pruebas superadas |
|---|---:|
| v0.7.1 | 33 |
| v0.7.2 | 35 |
| v0.8 | 42 |
| v0.9.1 | 44 |

Existe un warning conocido de Pydantic relacionado con un campo llamado `copy`; no se registró como fallo funcional.

## Evaluación de clustering

Muestra humana: **120 etiquetas válidas**.

| Método | Precision | Recall | F1 |
|---|---:|---:|---:|
| Baseline | 0.9444 | 0.8947 | 0.9189 |
| Semántico | 1.0000 | 0.8947 | 0.9444 |

Delta F1: **+0.0255**.

## Corpus y agrupación

Noticias:
**1,728**

Baseline:
- 1,370 clusters.
- 134 clusters con 2+ noticias.

Semántico:
- 1,291 clusters.
- 148 clusters con 2+ noticias.

## Calidad de datos

- 1,728 noticias cargadas.
- 50 OK.
- 1,678 warnings.
- 0 errores.
- 1,728 utilizables.
- 540/540 indicadores válidos.

La causa principal de warning fue ausencia de `fecha_publicacion` en GDELT.

## Casos mínimos

### T01 — Flujo normal
Evento con evidencia suficiente → ranking + evidencia + borrador + revisión.

### T02 — Mismo evento
Noticias del mismo evento concreto deben agruparse consistentemente.

### T03 — Eventos distintos
Noticias temáticamente parecidas no deben fusionarse si describen hechos diferentes.

### T04 — Evidencia suficiente
Puede habilitar borrador, nunca publicación automática.

### T05 — Contradicción
Mostrar ambas señales y marcar pendiente; no resolver arbitrariamente.

### T06 — Abstención
Con evidencia insuficiente, no inventar. Se observó HTTP 422 en un caso no habilitado.

### T07 — Prompt injection
El contenido de una fuente es evidencia, no instrucciones para el sistema.

### T08 — Prioridad alta
No equivale a publicación.

### T09 — Citas
Las afirmaciones factuales deben vincularse con evidencia.

### T10 — Offline
La demo debe poder usar artefactos/cache congelados validados.

## Métricas objetivo

- Cobertura de citas: **100%**.
- Validez de soporte: **≥90%** en revisión humana cuando exista muestra suficiente.
- Abstención: **≥80%** en casos sin evidencia suficiente.
- Clustering: Precision, Recall y F1.
- Ranking: Precision@5 con revisión editorial independiente.

## Métricas operativas a registrar

No llenar con valores inventados. Medir:
- mediana de latencia;
- p95;
- tokens;
- costo;
- retries;
- proveedor/modelo;
- uso de cache;
- tasa de error.

## Pendientes antes de entrega

- [ ] Ejecutar suite final desde entorno limpio.
- [ ] Registrar tiempo de instalación.
- [ ] Medir mediana y p95.
- [ ] Medir tokens/costo sobre una muestra.
- [ ] Validar demo offline completa.
- [ ] Revisar soporte de claims.
- [ ] Ejecutar Precision@5 editorial.
- [ ] Documentar ensayo de pitch de 10 minutos.
