"""Unit checks for benchmark scorer: synthetic fixtures only, no human review claimed."""
import importlib.util
from pathlib import Path
import pytest
path = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_editorial_benchmark.py"
spec = importlib.util.spec_from_file_location("editorial_benchmark", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
def _q(kind="insuficiente"):
    return [{"id":"Q1","tipo":kind}]
def test_no_predictions_not_evaluated():
    result=module.rate(_q(),[])
    assert result["estado"]=="NO_EVALUADO"
    assert result["abstencion_en_consultas_insuficientes"] is None
    assert result["t10_offline_integral"]=="NO_VERIFICADO"
def test_real_prediction_abstained():
    result=module.rate(_q(),[{"id":"Q1","answer":"","abstained":True,"claims":[],"evidence_catalog":[]}])
    assert result["abstencion_en_consultas_insuficientes"]==1.0
def test_invalid_citation_detected():
    result=module.rate(_q("sustentable"),[{"id":"Q1","answer":"Un dato","abstained":False,"claims":[{"text":"dato","evidence_ids":["FAKE"]}],"evidence_catalog":["NEWS-OK"]}])
    assert result["cobertura_estructural_citas"]==0.0
    assert result["referencias_desconocidas"]==1
def test_synthetic_judgment_excluded():
    p=[{"id":"Q1","answer":"dato","abstained":False,"claims":[{"text":"dato","evidence_ids":["NEWS-OK"]}],"evidence_catalog":["NEWS-OK"]}]
    result=module.rate(_q("sustentable"),p,[{"id":"Q1","procedencia":"simulacion","reviewer":"personaje ficticio","claim_verdicts":["sustentado"]}])
    assert result["juicios_simulados_excluidos"]==1
    assert result["validez_soporte_humana"] is None
def test_human_judgment_requires_provenance():
    p=[{"id":"Q1","answer":"dato","abstained":False,"claims":[{"text":"dato","evidence_ids":["NEWS-OK"]}],"evidence_catalog":["NEWS-OK"]}]
    with pytest.raises(ValueError):
        module.rate(_q("sustentable"),p,[{"id":"Q1","procedencia":"humano","reviewer":"Editor","claim_verdicts":["sustentado"]}])
