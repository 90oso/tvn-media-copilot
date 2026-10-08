NEWS_COLUMNS = [
    "id_noticia",
    "titulo",
    "url",
    "medio",
    "idioma",
    "fecha_publicacion",
    "fecha_deteccion",
    "fecha_extraccion",
    "tema",
    "origen",
    "alcance_texto",
]

INDICATOR_COLUMNS = [
    "pais_iso3",
    "indicador_id",
    "anio",
    "valor",
    "unidad",
    "fuente_url",
    "fecha_extraccion",
    "licencia",
]

# El documento indica explícitamente que `valor` es nullable.
INDICATOR_NULLABLE_COLUMNS = {"valor"}

NEWS_DATE_COLUMNS = [
    "fecha_publicacion",
    "fecha_deteccion",
    "fecha_extraccion",
]

INDICATOR_DATE_COLUMNS = [
    "fecha_extraccion",
]
