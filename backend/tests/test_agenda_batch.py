import pandas as pd

from app.core.settings import Settings
from app.services.agenda import build_agenda


class FakeRepo:
    def __init__(self):
        self.cluster_reads = 0

    def get_all_valid_news(self):
        return pd.DataFrame(
            [
                {
                    "id_noticia": "N1",
                    "titulo": "Panamá registra empleo en sector privado",
                    "url": "https://example.org/1",
                    "medio": "A",
                    "origen": "Fuente A",
                    "fecha_publicacion": "2026-09-30T10:00:00Z",
                    "fecha_deteccion": "2026-09-30T10:01:00Z",
                    "tema_final": "economía",
                    "alcance_texto": "titular/metadatos",
                    "cluster_semantic": "C1",
                },
                {
                    "id_noticia": "N2",
                    "titulo": "Panamá registra nuevas plazas de trabajo",
                    "url": "https://example.org/2",
                    "medio": "B",
                    "origen": "Fuente B",
                    "fecha_publicacion": "2026-09-30T11:00:00Z",
                    "fecha_deteccion": "2026-09-30T11:01:00Z",
                    "tema_final": "economía",
                    "alcance_texto": "titular/metadatos",
                    "cluster_semantic": "C1",
                },
                {
                    "id_noticia": "N3",
                    "titulo": "Canal anuncia actualización operativa",
                    "url": "https://example.org/3",
                    "medio": "C",
                    "origen": "Fuente C",
                    "fecha_publicacion": "2026-09-29T10:00:00Z",
                    "fecha_deteccion": "2026-09-29T10:01:00Z",
                    "tema_final": "logística/Canal",
                    "alcance_texto": "titular/metadatos",
                    "cluster_semantic": "C2",
                },
            ]
        )

    def get_panama_indicators(self):
        return pd.DataFrame(
            [
                {
                    "pais_iso3": "PAN",
                    "indicador_id": "SL.UEM.TOTL.ZS",
                    "anio": "2024",
                    "valor": "8.4",
                    "unidad": "porcentaje",
                    "fuente_url": "https://example.org/wb",
                    "licencia": "CC BY 4.0",
                }
            ]
        )

    def get_snapshot_reference(self):
        return pd.Timestamp("2026-09-30T23:59:59Z")

    def get_all_reviews(self):
        return {}

    def get_cluster_news(self, cluster_id):
        self.cluster_reads += 1
        raise AssertionError(
            "build_agenda no debe consultar cada cluster por separado"
        )


def test_agenda_uses_batch_read_not_n_plus_one():
    repo = FakeRepo()
    items = build_agenda(
        repo,
        Settings(),
        limit=2,
    )

    assert len(items) == 2
    assert repo.cluster_reads == 0
    assert {item["case_id"] for item in items} == {"C1", "C2"}
