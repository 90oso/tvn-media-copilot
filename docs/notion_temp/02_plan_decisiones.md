# 02 · Plan y decisiones

## Backlog inicial

| ID | Prioridad | Tarea | Estado | Responsable |
|---|---|---|---|---|
| M01 | Must | Repositorio y estructura | Hecho | TODO |
| M02 | Must | Contrato de datos | Hecho | TODO |
| M03 | Must | Carga de noticias | Hecho | TODO |
| M04 | Must | Carga de indicadores | Hecho | TODO |
| M05 | Must | Validación y calidad | Hecho | TODO |
| M06 | Must | Clasificación temática baseline | Hecho | TODO |
| M07 | Must | Agrupación baseline de noticias | Hecho | TODO |
| M08 | Must | Baseline simple documentado | Hecho | TODO |
| M09 | Must | Clustering semántico + evaluación contra cluster_humano | Implementado; pendiente datos reales | TODO |
| M10 | Must | Priorización R/I/U/N/E | Pendiente | TODO |
| M11 | Must | Ficha y evidencia | Pendiente | TODO |
| M12 | Must | Generación editorial | Pendiente | TODO |
| M13 | Must | Revisión humana | Pendiente | TODO |
| M14 | Must | T01–T10 | En curso | TODO |
| M15 | Must | Migración a Notion | Bloqueado externo | TODO |

## Decisiones

### DEC-001 · Priorizar modalidad TVN Media
**Estado:** aceptada para el MVP.  
**Razón:** completar primero un recorrido editorial convincente antes de banca.

### DEC-002 · Procesamiento batch sobre snapshot
**Estado:** aceptada para el MVP.  
**Razón:** prioriza reproducibilidad y una demo que no dependa de fuentes en vivo.

### DEC-003 · No detener el desarrollo por Notion
**Estado:** aceptada temporalmente.  
**Razón:** el host indicó avanzar y documentar mientras habilita Notion. Notion sigue siendo obligatorio.

### DEC-004 · Baseline temático por reglas/palabras clave
**Estado:** propuesta técnica aceptada para desarrollo.  
**Razón:** el reto exige comparar al menos una tarea de IA/NLP con un baseline simple. Este baseline
no se presenta como IA y permitirá medir luego el aporte del modelo semántico.

**Limitación deliberada:** usa el título y puede abstenerse ante ausencia de señal o empate.

## Cronología
- Día 1: datos, validación, organización, baseline, agrupación y ranking.
- Día 2: evidencia, generación, revisión, pruebas, demo y documentación.


### DEC-005 · Agrupación baseline trazable antes de embeddings
**Estado:** aceptada para desarrollo.  
**Razón:** permite cumplir una referencia simple y explicable antes de medir el aporte semántico.

### DEC-006 · Congelar embeddings para la demo
**Estado:** propuesta técnica.  
**Razón:** reduce dependencia de internet durante el pitch y mejora reproducibilidad.


### DEC-007 · Evaluación de clustering par-a-par
**Estado:** propuesta técnica implementada.  
**Razón:** los IDs de cluster humano y del sistema no tienen por qué coincidir. Se evalúa
para cada par de noticias si ambos métodos coinciden en `mismo evento` o `evento distinto`.

**Métricas:** precision, recall y F1 par-a-par.

### DEC-008 · No reportar métricas sintéticas como resultado final
**Estado:** aceptada.  
**Razón:** los fixtures solo validan el código. La métrica final requiere `cluster_humano`
creado mediante revisión humana.


### DEC-009 · Descartar Ollama/Qwen
Aceptada: mejora portabilidad y despliegue.

### DEC-010 · Gemini como único LLM del MVP
Aceptada: menor complejidad; `LLMProvider` mantiene desacoplamiento.

### DEC-011 · FastAPI + Next.js + DuckDB
Implementada como base profesional para GitHub y despliegue.

### DEC-012 · Contextualización conservadora
Implementada: no forzar relaciones con indicadores no sustentadas.

### DEC-013 · Reglas R/I/U/N/E versionadas
Propuesta implementada: el documento define componentes/pesos, no el cálculo de cada componente.


### DEC-014 · Dataset propio por recolección
**Estado:** implementado.  
**Razón:** aclaración del host: cada equipo debe construir sus datos.

### DEC-015 · Ventana de noticias 2025-10-02 → 2026-09-30
**Estado:** override operativo aceptado.  
**Razón:** instrucción posterior del host respecto al período.

### DEC-016 · No inferir fecha de publicación desde GDELT seendate
**Estado:** implementada.  
**Razón:** el contrato distingue publicación de detección.

### DEC-017 · Cuadrícula Banco Mundial de 540 filas según dimensiones enumeradas
**Estado:** implementada con advertencia.  
**Razón:** 6 países × 6 indicadores × 15 años = 540; el valor 1,350 del documento contradice
sus propias dimensiones. La discrepancia queda documentada y no se rellenan dimensiones inventadas.


### DEC-018 · Seleccionar clustering semántico para el MVP
**Estado:** aceptada tras evaluación humana.  
**Criterio:** mayor F1 par-a-par contra `cluster_humano`.  
**Resultado observado por el equipo:** baseline F1=0.9189; semántico F1=0.9444; ΔF1=+0.0255.  
**Limitación:** resultado basado en 120 noticias etiquetadas; no se extrapola sin cautela a todo el corpus.

### DEC-019 · Clasificación semántica por centroides como ampliación del baseline
**Estado:** propuesta implementada.  
**Razón:** el baseline temático clasifica una fracción limitada del corpus. Se reutilizan embeddings
congelados y etiquetas baseline como semillas, sin añadir otro proveedor ni nueva descarga de modelo.
Los umbrales deben validarse.


### DEC-020 · Generación editorial estructurada
**Estado:** aceptada para MVP.  
**Decisión:** Gemini produce JSON por modalidad y Python valida límites, campos y trazabilidad.  
**Razón:** no delegar al LLM las reglas duras de formato y citación.

### DEC-021 · Contradicciones como señal, no veredicto
**Estado:** aceptada.  
**Decisión:** reglas léxicas transparentes marcan contradicciones potenciales; el sistema muestra ambas
versiones y exige verificación humana. Nunca clasifica automáticamente una fuente como verdadera/falsa.

### DEC-022 · Cache de generación para demo offline
**Estado:** aceptada.  
**Decisión:** solo se cachean borradores que ya pasaron validación estructural y de evidence_id. La clave
del cache incluye una huella del paquete de evidencia para evitar reutilizar borradores obsoletos.
