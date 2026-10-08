import pandas as pd

from tvn_copilot.services.classification import (
    OFFICIAL_TOPICS,
    classify_dataframe_baseline,
    classify_title_baseline,
)


def test_baseline_classifies_logistics():
    result = classify_title_baseline(
        "El Canal de Panamá reporta tránsito de buques y carga"
    )
    assert result.topic == "logística/Canal"
    assert result.status == "clasificado"
    assert result.match_count >= 1


def test_baseline_abstains_when_no_keyword_signal():
    result = classify_title_baseline(
        "Autoridades ofrecen conferencia durante la mañana"
    )
    assert result.topic is None
    assert result.status == "sin_clasificar"


def test_baseline_does_not_overwrite_reference_topic():
    df = pd.DataFrame(
        [
            {
                "titulo": "Panamá registra nueva cifra de inflación",
                "tema": "economía",
            }
        ]
    )
    out = classify_dataframe_baseline(df)

    assert out.loc[0, "tema"] == "economía"
    assert out.loc[0, "tema_baseline"] == "economía"
    assert out.loc[0, "tema_baseline"] in OFFICIAL_TOPICS
