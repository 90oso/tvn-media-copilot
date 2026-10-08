# Reporte baseline de clasificación temática

- Generado UTC: `2026-10-07T20:08:14.432430+00:00`
- Versión: `keyword-rules-v0.1`
- Entrada: `data\processed\noticias_validated.csv`
- Filas: **1728**

## Propósito

Este baseline simple se conserva para compararlo posteriormente contra una capacidad NLP/ML. **No se presenta como IA**.

## Distribución

| Tema baseline | Registros |
|---|---:|
| sin_clasificar | 1487 |
| logística/Canal | 100 |
| economía | 68 |
| turismo | 52 |
| eventos naturales | 8 |
| regulación | 7 |
| servicios públicos | 6 |

## Estados

| Estado | Registros |
|---|---:|
| sin_clasificar | 1474 |
| clasificado | 241 |
| empate | 13 |

## Evaluación contra `tema`

- Métricas no disponibles: No hay etiquetas de referencia válidas. Las métricas deben calcularse sobre etiquetas humanas.

Las métricas finales deben calcularse contra etiquetas creadas por revisión humana.

## Limitaciones

- Solo usa el título.
- No interpreta contexto o polisemia.
- Puede abstenerse si no encuentra señal suficiente.
- Puede abstenerse si dos o más temas empatan.
- Las palabras clave son una propuesta del equipo.

## Siguiente comparación

Implementar una clasificación o similitud semántica con NLP/ML y comparar cobertura, macro-F1/precision/recall y errores cualitativos.