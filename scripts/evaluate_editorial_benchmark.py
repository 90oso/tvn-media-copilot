"""Evaluación editorial reproducible; stdlib, sin llamadas a Gemini o a Internet.

Los juicios de procedencia 'simulacion' se excluyen SIEMPRE de validez factual humana.
Un resultado vacío o no medido se registra como null; no se transforma en éxito.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
            raise ValueError(f"{path}:{no}: cada fila necesita id")
        rows.append(obj)
    seen = [row["id"] for row in rows]
    if len(seen) != len(set(seen)):
        raise ValueError(f"IDs duplicados en {path}")
    return rows


def rate(questions: list[dict], responses: list[dict], judgments: list[dict] | None = None,
         ranking_review: dict | None = None) -> dict:
    questions_by_id = {x["id"]: x for x in questions}
    predictions = {x["id"]: x for x in responses}
    if set(predictions) - set(questions_by_id):
        raise ValueError("Hay respuestas para consultas inexistentes")
    judgments_by_id = {x["id"]: x for x in judgments or []}
    structural_numerator = structural_denominator = 0
    invalid_citation_ids = 0
    abstention_correct = abstention_total = 0
    false_abstentions = supported_total = 0
    claims_with_human_verdict = human_supported = human_rejected = 0
    reviewed_queries = 0
    simulated_judgments = 0
    for qid, question in questions_by_id.items():
        response = predictions.get(qid)
        if response is None:
            continue
        abstained = response.get("abstained")
        if not isinstance(abstained, bool):
            raise ValueError(f"{qid}: abstained debe ser boolean")
        kind = question.get("tipo")
        if kind == "insuficiente":
            abstention_total += 1
            if abstained and not str(response.get("answer") or "").strip():
                abstention_correct += 1
        if kind == "sustentable":
            supported_total += 1
            false_abstentions += int(abstained)
        catalog = set(response.get("evidence_catalog") or [])
        claims = response.get("claims") or []
        if not isinstance(claims, list):
            raise ValueError(f"{qid}: claims no es lista")
        for claim in claims:
            structural_denominator += 1
            ids = claim.get("evidence_ids") or []
            if ids and all(isinstance(cid, str) and cid in catalog for cid in ids):
                structural_numerator += 1
            invalid_citation_ids += sum(cid not in catalog for cid in ids)
        judgment = judgments_by_id.get(qid)
        if judgment is not None:
            if judgment.get("procedencia") != "humano":
                simulated_judgments += 1
                continue
            if not all(judgment.get(k) for k in ("reviewer", "reviewed_at", "source_url")):
                raise ValueError(f"{qid}: juicio humano sin revisor, fecha o fuente")
            verdicts = judgment.get("claim_verdicts") or []
            if len(verdicts) != len(claims) or any(v not in ("sustentado", "no_sustentado") for v in verdicts):
                raise ValueError(f"{qid}: cada claim requiere dictamen binario")
            reviewed_queries += 1
            claims_with_human_verdict += len(verdicts)
            human_supported += verdicts.count("sustentado")
            human_rejected += verdicts.count("no_sustentado")
    precision_at_5 = None
    ranking_note = "sin selección editorial independiente real"
    if ranking_review and ranking_review.get("procedencia") == "humano":
        if not all(ranking_review.get(x) for x in ("reviewer", "reviewed_at")):
            raise ValueError("Ranking sin revisor o fecha")
        predicted = ranking_review.get("top5")
        gold = ranking_review.get("selected_by_editor")
        if not (isinstance(predicted, list) and isinstance(gold, list) and len(predicted) == 5 and len(set(predicted)) == 5):
            raise ValueError("Ranking debe contener cinco casos distintos y selección del editor")
        precision_at_5 = len(set(predicted) & set(gold)) / 5
        ranking_note = "evaluación editorial humana declarada"
    return {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "EVALUADO_PARCIALMENTE" if responses else "NO_EVALUADO",
        "tipo_evaluacion": "resultados_calculados_no_sustituye_verificacion_independiente",
        "consultas_programadas": len(questions),
        "consultas_con_respuesta": len(responses),
        "consultas_sin_resultado": len(questions)-len(responses),
        "cobertura_estructural_citas": structural_numerator / structural_denominator if structural_denominator else None,
        "afirmaciones_con_cita_valida": structural_numerator,
        "afirmaciones_emitidas": structural_denominator,
        "referencias_desconocidas": invalid_citation_ids,
        "abstencion_en_consultas_insuficientes": abstention_correct / abstention_total if abstention_total else None,
        "casos_insuficientes_respondidos": abstention_total,
        "falsas_abstenciones_en_potencialmente_sustentables": false_abstentions if supported_total else None,
        "sustentables_respondidas": supported_total,
        "validez_soporte_humana": human_supported / claims_with_human_verdict if claims_with_human_verdict else None,
        "afirmaciones_revisadas_por_humano": claims_with_human_verdict,
        "afirmaciones_rechazadas_por_humano": human_rejected,
        "consultas_revisadas_por_humano": reviewed_queries,
        "juicios_simulados_excluidos": simulated_judgments,
        "precision_at_5_humana": precision_at_5,
        "precision_at_5_nota": ranking_note,
        "t07_modelo_real": "NO_VERIFICADO",
        "t10_offline_integral": "NO_VERIFICADO",
        "persistencia_produccion": "NO_VERIFICADO",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--questions", type=Path, default=Path("data/benchmark/dev_40.jsonl"))
    p.add_argument("--responses", type=Path, help="Predicciones guardadas (no se realizan solicitudes)")
    p.add_argument("--judgments", type=Path, help="Revisiones humanas reales, opcionales")
    p.add_argument("--ranking-review", type=Path, help="Selección editorial independiente JSON")
    p.add_argument("--output", type=Path, default=Path("reports/entrega_final/benchmark_resultado.json"))
    args = p.parse_args()
    questions = load_jsonl(args.questions)
    responses = load_jsonl(args.responses) if args.responses else []
    judgments = load_jsonl(args.judgments) if args.judgments else []
    ranking = json.loads(args.ranking_review.read_text(encoding="utf-8")) if args.ranking_review else None
    report = rate(questions, responses, judgments, ranking)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
