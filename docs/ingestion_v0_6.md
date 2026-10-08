# Ingesta real v0.6

## Fuente de verdad

El documento del reto define como núcleo Media:

- A · Noticias públicas: TVN RSS + GDELT DOC 2.0.
- B · Banco Mundial: indicadores oficiales.

El host aclaró posteriormente que cada equipo arma su dataset y que la ventana válida de noticias
es **2025-10-02 a 2026-09-30**. Esta aclaración se registra como override operativo.

## Flujo

```text
TVN RSS ───────────┐
                   ├─> raw/ ─> normalización ─> dedupe URL ─> noticias.csv/parquet
GDELT DOC 2.0 ─────┘

World Bank API ───────> raw lógico ─> cuadrícula completa ─> indicadores.csv/parquet

Todos ─> manifest.json + fuentes.json + hashes SHA-256 + cobertura efectiva
```

## TVN

Se consumen únicamente metadatos RSS. No se descarga cuerpo completo, imagen ni video.

La fecha del RSS se guarda como `fecha_publicacion`.
`fecha_deteccion` corresponde al momento en que nuestro collector detecta el item.

**Limitación:** no se asume que el RSS conserve todo el histórico.

## GDELT

Se utiliza DOC 2.0 en ventanas temporales y `ArtList`.

`seendate` se guarda en `fecha_deteccion`.

No se copia `seendate` a `fecha_publicacion`. Si no existe una fecha de publicación distinta
en la respuesta utilizada, `fecha_publicacion` queda nula.

Si una ventana alcanza `maxrecords=250`, el manifest registra una advertencia para reducir la
ventana y volver a extraer.

### Riesgo de cobertura histórica

La documentación pública de GDELT DOC 2.0 describe una ventana de búsqueda limitada/rodante.
Por ello, el collector **no promete** que una consulta ejecutada hoy pueda recuperar todo
2025-10-02 → 2026-09-30. Se debe registrar cobertura efectiva y cualquier vacío.

## Banco Mundial

Países:
PAN, CRI, COL, DOM, MEX, GTM.

Indicadores:
- NY.GDP.MKTP.KD.ZG
- FP.CPI.TOTL.ZG
- SL.UEM.TOTL.ZS
- SP.POP.TOTL
- IT.NET.USER.ZS
- NE.EXP.GNFS.ZS

Años:
2010–2024.

Se completa la cuadrícula incluso cuando el API devuelve valores nulos.

### Contradicción detectada

El documento enumera 6 países × 6 indicadores × 15 años, lo cual produce **540 combinaciones**,
pero también declara una cuadrícula de **1,350**.

La implementación sigue las dimensiones explícitamente enumeradas y registra la discrepancia
en `manifest.json`. No se inventan países, indicadores ni años para alcanzar 1,350.

## Salidas

```text
data/snapshot/
├── noticias.csv
├── noticias.parquet
├── indicadores.csv
├── indicadores.parquet
├── fuentes.json
└── manifest.json
```

## Ejecución

```powershell
Copy-Item .env.example .env
pip install -r backend/requirements.txt
$env:PYTHONPATH="backend"
python scripts/ingest_real_data.py
```

Luego:

```powershell
python scripts/validate_snapshot.py `
  --news data/snapshot/noticias.csv `
  --indicators data/snapshot/indicadores.csv
```


## Ajuste v0.6.1 de validación

Una fecha de publicación ausente no significa necesariamente dato inválido. Para fuentes donde
solo tenemos fecha de detección, se conserva `fecha_publicacion = NULL` y se registra un warning.
Esto evita excluir masivamente registros GDELT del pipeline sin falsificar la fecha original.


## Ajuste v0.6.2: fecha efectiva para clustering

El corpus real confirmó que GDELT conserva `fecha_deteccion` pero no una
`fecha_publicacion` independiente. Los motores de clustering ahora usan una fecha operativa:

1. publicación si existe;
2. detección si publicación es desconocida.

Esto solo se usa para calcular proximidad temporal. Nunca modifica el contrato ni rellena
`fecha_publicacion`.
