# Diccionario de datos mínimo

## noticias.csv

| Campo | Descripción operativa |
|---|---|
| id_noticia | ID estable de la noticia |
| titulo | Titular |
| url | URL de origen |
| medio | Medio |
| idioma | Idioma |
| fecha_publicacion | Fecha de publicación |
| fecha_deteccion | Fecha de detección; no confundir con publicación |
| fecha_extraccion | Fecha de extracción |
| tema | Tema editorial |
| origen | Procedencia/origen |
| alcance_texto | Alcance del contenido disponible, por ejemplo metadatos |

## indicadores.csv

| Campo | Descripción operativa |
|---|---|
| pais_iso3 | Código ISO3 |
| indicador_id | ID del indicador |
| anio | Año del dato |
| valor | Valor; puede ser nulo |
| unidad | Unidad |
| fuente_url | URL de la fuente |
| fecha_extraccion | Fecha de extracción |
| licencia | Licencia/condiciones |

## Regla crítica

Los nulos se conservan. Una ausencia de información no se reemplaza por cero.
