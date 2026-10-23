# Posicionamiento comercial — Media Copilot

## Veredicto
**Potencial alto como inteligencia sectorial B2B; el motor existente requiere producto multiusuario y nuevas fuentes.** Competidores de monitoreo de medios/PR como Meltwater, Cision y Brandwatch ya cubren el mercado amplio: el enfoque viable es nicho, trazabilidad y entregables para cada comprador.

## Herencia del reto
El proyecto original estuvo dirigido a TVN. La nueva presentación comercial no utiliza ni sugiere asociación con TVN; TVN RSS, GDELT y Banco Mundial permanecen atribuidos como **fuentes** en el producto histórico. No usar la marca TVN en la oferta comercial sin autorización. Revisar derechos de reproducción y API de cada fuente.
- Backend: FastAPI, ingesta, normalización, agrupación y ranking explicable, generación condicionada por evidencia y revisión humana.
- Frontend: Next.js/React, fichas, Radar y espacio de revisión.
- Demo aislada: `docs/index.html`, sin noticias reales ni conexión a backend. Perfiles, palabras clave, filtros por rango de fechas, evidencia, borrador determinista y exportación.

## Cuatro productos posibles (elegir UNO para el primer piloto)
- Comunicación corporativa: alertas por marca, crisis y sector; ficha de evidencia y brief diario.
- Consultoría: vigilancia competitiva/mercado, señales regulatorias, brief semanal para clientes.
- Independientes: plan de investigación, reportes exportables, precio por proyecto.
- Redacciones: agenda periodística; revisión editorial obligatoria.

## Brechas técnicas para producción
1. Fuentes por espacio de trabajo: URLs RSS, importación CSV, proveedores con licencias; configuración de periodo consultado y periodo de actualización.
2. **Implementado en esta rama:** filtros `date_from`/`date_to` del servidor y controles de búsqueda temporal en Next.js. **Pendiente:** filtros por organización, ingesta histórica configurable, recuperación de faltantes y calibración de precisión. No confundir fecha de detección con publicación.
3. Separación multiempresa, permisos, SSO/MFA, cuotas, gestión de coste de LLM y almacenamiento persistente.
4. Buscador reproducible: normalización de tildes, sinónimos, tokens, BM25/embeddings; tests en consultas donde hay coincidencias ("empleo") y falsos negativos.
5. Deduplicación, agrupación y rankings calibrados con evaluación humana en datos del segmento objetivo.
6. Contratos/licencias para consultar, resumir y visualizar contenido de terceros; enlaces al original, no republicación indiscriminada.
7. Alertas programadas, exportación PDF/CSV/Markdown, dashboards por sector, historial de decisiones y revisión.
8. Panel de configuración de fuentes y filtros; explainability de puntuaciones, no presentarlas como probabilidades de veracidad.

## Experimento de mercado
Primero 5-10 compradores potenciales de un mismo segmento; enseñar un informe ficticio, acordar fuente y KPI. Piloto con datos licenciados/publicables, medir relevancia de alertas, minutos ahorrados por brief, tasa de citas verificables y repetición semanal. Evitar competir por volumen masivo de fuentes.

## Competencia
https://www.shadow.inc/resources/best-media-monitoring-tools-pr-agencies
https://debriefing.io/guides/media-monitoring-tools

## Nombre
«Media Copilot» es descriptivo provisional. Comprobar registros comerciales, marca y dominio antes de su lanzamiento público.
