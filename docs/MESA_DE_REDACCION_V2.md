# Mesa de Redacción · Refinamiento visual y filtro de idioma

## Qué cambia

- Identidad cromática **inspirada** en la presencia digital de TVN Media Panamá: azules profundos, azul brillante, cian y superficies frías. No constituye una reproducción certificada de un manual oficial de marca.
- El espacio de **Decisión editorial** tiene anchura mínima de 460 px en monitores amplios; en ventanas menores de 1570 px pasa a una segunda fila con campos de revisión/generación en columnas legibles. En móviles queda apilado.
- Se agrandan títulos, texto editorial, campos, botones y borradores. Sigue disponible el modo oscuro.
- En Radar aparece filtro de idioma: **Titulares en español** (predeterminado) y **Todos los idiomas**.

## ¿Por qué pueden aparecer noticias en ruso?

El conjunto incluye TVN RSS y resultados de GDELT, que reúne publicaciones en distintos idiomas. El campo `idioma` se conserva y no se debe reinterpretar ni traducir una noticia sin verificación. No es evidencia de un bug de decodificación por sí solo.

El filtro nuevo restringe **el descubrimiento de eventos en el Radar** cuando el idioma está etiquetado como español; no modifica ni elimina datos del snapshot. El expediente original puede conservar referencias de otros idiomas que participaron en su agrupación, y la pantalla informa de ese hecho. La comprobación adicional de alfabeto cirílico ayuda a detener títulos obviamente mal etiquetados, pero no sustituye la detección profesional de idioma.

Para hacer reproducible la búsqueda también desde HTTP:

- `GET /explore?language=es&limit=20`
- `GET /explore?language=all&limit=20`
- `GET /agenda?language=es&limit=5`
- `GET /agenda?limit=5` **mantiene su comportamiento anterior** (todos los idiomas), para no alterar integraciones, scripts ni cachés que ya funcionan.

En el backend, el ranking se calcula sobre el expediente completo y se mantiene la regla P=30R+25I+20U+15N+10E. El filtro afecta la selección y el titular representativo del evento, no simula una verificación factual.

## Instalación y verificación rápida

Desde la raíz del repositorio, descomprimir el ZIP **manteniendo las carpetas** `backend/`, `frontend/` y `docs/`. Antes de aplicar, revisar `git status`; no sobrescribir cambios propios pendientes sin revisarlos.

1. Activar entorno virtual y correr `pytest -q`.
2. Iniciar FastAPI con `run_backend.bat`; verificar `http://localhost:8000/health` y `http://localhost:8000/explore?language=es&limit=3`.
3. En otra terminal: `cd frontend; npm run build; npm run dev -- -p 3000`. Si el puerto 3000 está ocupado, detener la instancia anterior.
4. Probar alternar idioma del radar. No debe aparecer un evento enteramente en ruso cuando se selecciona «Titulares en español»; sí puede aparecer al elegir «Todos los idiomas».
5. Probar en ventanas de 1920, 1366, 1024 y 390 px; especialmente campos y botones de dictamen.

## Límites

- El filtro se basa en la etiqueta existente `idioma`, con protección básica frente a titulares en cirílico etiquetados erróneamente como español. Registros sin etiqueta no aparecen en el filtro de español.
- El expediente puede incluir fuentes en otros idiomas; esto se declara explícitamente en pantalla. No se altera la evidencia original ni se recomputa la prioridad a partir de una traducción.
- Se conserva toda la lógica de generación, borradores, aprobación y estado de publicación. No se introduce publicación automática.
