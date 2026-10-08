# Registro de decisiones — TVN Media Copilot

## D001 — Media primero
**Estado:** aceptada.  
Completar TVN Media end-to-end antes de extender a otro dominio. Beneficio: reducir dispersión y asegurar un MVP demostrable.

## D002 — FastAPI + Next.js + DuckDB
**Estado:** aceptada.  
Stack ligero, local y rápido de implementar.

## D003 — Fuentes públicas reproducibles
**Estado:** aceptada.  
Fuentes: TVN RSS, GDELT DOC 2.0 y World Bank API.

## D004 — Ventana 2025-10-02 a 2026-09-30
**Estado:** aceptada.  
Se usa como periodo operativo del corpus de noticias.

## D005 — Mantener explícita la discrepancia de indicadores
**Estado:** aceptada.  
La implementación usa 6 países × 6 indicadores × 15 años = **540** observaciones. Una cifra distinta en documentación de referencia se registra como discrepancia y no se sustituye silenciosamente.

## D006 — `fecha_deteccion` como fallback
**Estado:** aceptada.  
Si falta `fecha_publicacion`, se usa `fecha_deteccion` como fecha efectiva sin borrar el warning.

## D007 — Conservar baseline
**Estado:** aceptada.  
El baseline permanece para comparar y demostrar el aporte del componente semántico.

## D008 — Seleccionar clustering semántico
**Estado:** aceptada para MVP.  
Sobre 120 etiquetas humanas: F1 baseline 0.9189; F1 semántico 0.9444.

## D009 — Embeddings multilingües
**Estado:** aceptada.  
Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

## D010 — Corrección PyTorch/Windows
**Estado:** aceptada.  
Precargar `torch` para evitar el error observado de `c10.dll`.

## D011 — Gemini como único LLM del MVP
**Estado:** aceptada.  
Se descartó Ollama/Qwen para este MVP con el fin de reducir complejidad. Modelo probado: `gemini-3.6-flash`.

## D012 — Sin fallback silencioso de modelo
**Estado:** aceptada.  
Los errores transitorios disparan retry; no se cambia automáticamente de modelo.

## D013 — Evidence-first
**Estado:** aceptada.  
Orden lógico:
`retrieval → evidencia → estado de evidencia → ranking → generación`.

## D014 — Abstención por falta de evidencia
**Estado:** aceptada.  
El sistema puede responder HTTP 422 en lugar de generar afirmaciones no respaldadas.

## D015 — Prioridad != publicación
**Estado:** aceptada.  
Un score alto solo prioriza atención editorial. No autoriza publicación.

## D016 — Mantener fórmula oficial
**Estado:** aceptada.  
`P = 30R + 25I + 20U + 15N + 10E`.

## D017 — Salidas estructuradas
**Estado:** aceptada.  
Brief ≤250 palabras, 3 preguntas, guion 45–60 s, copy ≤80 palabras y evidencia validada.

## D018 — Cache para demo offline
**Estado:** aceptada.  
Se permite reutilizar una generación validada cuando coincide la huella de evidencia, marcándola como cached.

## D019 — Eliminar patrón N+1
**Estado:** aceptada.  
La agenda usa cargas masivas y análisis agrupado en memoria.

## D020 — Git desde el estado consolidado real
**Estado:** aceptada.  
No se retrofechan ni falsifican commits. El primer commit establece el baseline consolidado; v0.1–v0.9.1 quedan documentadas como historia reconstruida.
