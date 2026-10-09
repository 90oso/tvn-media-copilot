# Estado real de la evaluación — documento posterior a la entrega

| Área | Evidencia existente | Ampliación necesaria |
|---|---|---|
| T01 | Fixture local de fecha inválida y nulos | Anexar log y caso final |
| T02 | Agrupación sintética sin triplicar procedencia | Contrastar fuentes originales |
| T03 | Fecha publicación/detección preservada | Captura recirculación real |
| T04 | Año/unidad Banco Mundial en fixture | Verificar uso en noticia real |
| T05 | Detección sintética de contradicción | Revisión del conflicto real |
| T06 | Regla de abstención local | Consulta real sin respuesta y tasa |
| T07 | Inspección del prompt sintética | Modelo real: NO VERIFICADO |
| T08 | Cálculo ranking y no publicación | Auditoría de permisos del backend |
| T09 | IDs de citas presentes en fixture | Revisión semántica independiente |
| T10 | Cache recuperable localmente sin red | Plataforma íntegramente offline: NO VERIFICADO |

**Pruebas históricas conocidas:** 67 tests locales pasaron en Windows en commit 11fffe0; eso no certifica nuevos commits.
**Auditoría remota histórica:** 9 HTTP 200 y 7 errores de 16 solicitudes; mediana de agenda 31.7706 s y p95 44.9912 s en 8 respuestas correctas.
**Persistencia después de reinicio Render:** NO VERIFICADO.

**Benchmark:** data/benchmark/dev_40.jsonl contiene 40 *consultas propuestas*, no 40 respuestas ejecutadas. Ejecutar scripts/evaluate_editorial_benchmark.py sobre respuestas reales. Mantener reserva holdout 20 fuera del repo. No inventar etiquetas humanas.

**Acceso del jurado a Notion:** confirmado por el equipo.
**Fecha de esta mejora:** posterior a la entrega; no representar cambios retroactivos como entregados antes del plazo.
