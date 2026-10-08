# Mesa de Redacción — TVN Media Copilot

## Propósito

Rediseño **funcional** del MVP editorial: **Radar → Cuaderno de evidencia → Decisión humana**. No cambia la fórmula del ranking, el proveedor Gemini, el pipeline NLP/ML ni los datos congelados. No incluye publicación automática.

## Funcionalidad entregada

- **Radar:** Top 5 original y exploración del corpus mediante `GET /explore`, búsqueda por titulares y metadatos en español, filtro de sección y filtro de suficiencia de evidencia. Hasta 30 casos por consulta (no es paginación exhaustiva).
- **Preguntas genéricas de agenda:** una consulta como «¿Qué cinco temas merecen revisión para la agenda de Panamá y por qué?» se interpreta como solicitud del Top 5 priorizado.
- **Abstención de búsqueda:** si no hay coincidencias, la interfaz indica que no puede responder con los metadatos disponibles. No fabrica una respuesta ni una cifra.
- **Cuaderno:** titular protagonista, identificación del caso, diferencia entre **fecha de publicación** y **fecha de detección**, referencias periodísticas, contexto oficial, faltantes, contradicciones potenciales y score explicable.
- **Evidencia en foco:** permite inspeccionar un ID/campo y abrir/copiar la referencia.
- **Decisión:** brief, guion, copy digital, recuperación de cache, campo de revisor y revisión humana. El botón **Aprobar borrador** de la UI exige evidencia suficiente y un borrador cargado en la sesión.
- **Diseño:** identidad editorial, diseño adaptable a pantallas, modo claro/oscuro, sin dependencias visuales nuevas ni fuentes externas; la demo es apta para ejecutarse sin red para esos recursos.

## API nueva

`GET /explore?q=<texto>&topic=<tema>&evidence=<estado>&limit=20`

Parámetros:

| Campo | Uso |
|---|---|
| `q` | Palabras o pregunta orientativa en español; máximo 240 caracteres |
| `topic` | Tema editorial exacto de la taxonomía; opcional |
| `evidence` | `insuficiente`, `parcial` o `suficiente para el borrador`; opcional |
| `limit` | De 1 a 30; por defecto 20 |

Respuesta: `{items, count, total_matches, abstained, note, search_mode}`. Cada `item` conserva `attention`, `workflow` y `evidence_package` y añade `headline`, `source`, `date`, `date_origin` y `search_matches`.

**Importante:** la búsqueda implementada es **léxica e interpretable** sobre titulares/metadatos; no es un agente de preguntas y respuestas libre ni una validación de verdad. Una coincidencia no implica corroboración. Cuando hay una consulta, las coincidencias se ordenan primero por cantidad de términos encontrados y después por el puntaje oficial; **no se alteran los pesos R/I/U/N/E**.

El endpoint usa cargas masivas, igual que la agenda v0.9.1, para evitar reintroducir el patrón N+1.

## Instalación del parche

Desde la carpeta raíz del repositorio que contiene `backend/` y `frontend/`, colocar el ZIP del parche en esa carpeta y ejecutar:

```powershell
Expand-Archive -LiteralPath .\tvn_media_mesa_de_redaccion_patch.zip -DestinationPath . -Force
```

No reemplaza `.env`, `README.md`, `data/`, `reports/` ni los JSON del cache.

Reiniciar ambos servidores; `next dev` en caliente no sustituye el reinicio del backend para cargar la ruta `/explore`.

```powershell
# Terminal A: backend
.\.venv\Scripts\Activate.ps1
.\run_backend.bat

# Terminal B: frontend
cd frontend
npm install
npm run build
npm run dev
```

Abrir `http://localhost:3000`.

## Pruebas de aceptación manual (antes del commit)

1. Ingresar `empleo` y buscar. Deben listarse casos coincidentes. Abrir el titular, inspeccionar su fuente y verificar el campo/ID.
2. Buscar «¿Qué cinco temas merecen revisión para la agenda de Panamá y por qué?». Debe presentar una agenda priorizada, no una respuesta inventada.
3. Consultar `fusión nuclear cuántica`. Debe informar que no encuentra evidencia y abstenerse.
4. Filtrar por `economía` o por evidencia `parcial`; abrir un caso y comprobar estado/restricción de borrador.
5. Abrir `EVT-S-f0545cf214`, si el snapshot lo conserva y sigue elegible, y verificar la recuperación de `brief`, `script` y `digital` en el cache.
6. En un caso elegible, generar/recuperar un borrador, indicar revisor, registrar una corrección con nota y confirmar que la decisión persiste al recargar.
7. Verificar que **Aprobar borrador** no esté disponible cuando la evidencia es parcial.
8. Probar tamaños de ventana y modo oscuro.

## Pruebas automáticas

En el código de referencia del parche: `51 passed, 1 warning`, con prueba HTTP de `/explore`.

```powershell
pytest -q
```

La compilación completa de Next (`npm run build`) **no fue verificable en el entorno de preparación** por indisponibilidad de `registry.npmjs.org`. Se comprobó la sintaxis TSX; se debe ejecutar el build local antes de versionar. El warning de Pydantic sobre el campo `copy` es conocido y no afecta directamente este parche.

## Limitaciones conscientes / pendientes del reto

- No se ha construido un chat de respuesta libre con citas por afirmación para consultas arbitrarias. `/explore` solo recupera casos.
- La independencia editorial de medios **no queda comprobada** por contar dominios/orígenes; la interfaz lo advierte, pero la heurística backend para suficiencia de evidencia no cambia aún.
- La UI requiere un borrador cargado para permitir aprobar; el backend actual **todavía no vincula la aprobación a un ID/hash inmutable del borrador**. No presentar esta UX como control de auditoría completo.
- No se han creado ni aprobado los benchmarks T01–T10, ni las métricas humanas exigidas en el reto.
- El espacio Notion sigue siendo una entrega oficial independiente del frontend. Integración automática con Notion no es necesaria.
- La búsqueda no garantiza recencia real: está limitada al snapshot. `date_origin` distingue publicación de detección para evitar mezclar ambas.
