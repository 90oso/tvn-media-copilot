# Benchmark editorial — desarrollo y reserva
Este directorio contiene **40 consultas sintéticas propuestas** (`dev_40.jsonl`), no 40 respuestas realizadas ni evaluadas.
Distribución: 20 potencialmente sustentables, 7 ambiguas, 7 insuficientes, 6 adversariales.
La etiqueta `sustentable` es una **intención de diseño**, no prueba de que exista contenido real que la responda; si la evidencia no está presente, la salida correcta es abstenerse.

## Conjunto reservado
El protocolo del reto prevé **20 consultas adicionales**: 10 sustentables, 3 ambiguas, 3 sin respuesta y 4 adversariales.
La reserva **no debe subirse al repositorio público**, ni mezclarse con prompts entregados al agente durante el desarrollo.
Conservarla fuera del repositorio hasta su evaluación. No inventar una puntuación para la reserva.

## Ejecución reproducible
1. Ejecutar el agente con cada consulta y guardar `predicciones.jsonl` con `id`, `answer`, `abstained`, `claims`, `evidence_catalog`.
2. Hacer evaluación editorial independiente y guardar `revisiones.jsonl` con `id`, `procedencia: humano`, `reviewer`, `reviewed_at`, `verified_claims` y `claim_verdicts`, solo después de revisión auténtica.
3. Ejecutar:

```powershell
python scripts/evaluate_editorial_benchmark.py --questions data/benchmark/dev_40.jsonl --responses reports/entrega_final/predicciones.jsonl --judgments reports/entrega_final/revisiones.jsonl --output reports/entrega_final/benchmark_real.json
```

**Nunca atribuir evaluaciones sintéticas a personas reales** ni registrar T07, T10 o persistencia real como completadas por una prueba simulada.
Las métricas no estimables quedan `null`, con su razón.
