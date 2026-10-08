from pathlib import Path

from app.schemas.editorial import BriefDraft, DigitalDraft, EditorialClaim
from app.schemas.evidence import EvidenceItem, EvidencePackage
from app.services.editorial_generation import (
    _quality_for_mode,
    cache_path,
    load_cache,
    save_cache,
    GeneratedEditorial,
)


def package():
    return EvidencePackage(
        case_id="C1",
        topic="economía",
        news_ids=["N1"],
        evidence=[
            EvidenceItem(
                evidence_id="NEWS-1",
                source_type="news",
                source_name="Fuente",
                field="titulo",
                value="Titular",
            )
        ],
        contradictions=[],
        evidence_state="suficiente para el borrador",
        independent_provenances=2,
        rules_version="v",
    )


def test_brief_quality_has_full_citation_coverage():
    draft = BriefDraft(
        proposed_title="Título",
        public_interest="Interés",
        summary="Resumen corto.",
        claims=[
            EditorialClaim(
                type="hecho",
                text="Hecho trazable",
                evidence_ids=["NEWS-1"],
            )
        ],
        investigation_questions=["Q1", "Q2", "Q3"],
        sources_used=["NEWS-1"],
        pending_checks=[],
    )
    quality = _quality_for_mode("brief", draft, package())
    assert quality["citation_coverage"] == 1.0
    assert quality["within_word_limit"] is True


def test_digital_copy_over_80_words_is_rejected():
    draft = DigitalDraft(
        copy=" ".join(["palabra"] * 81),
        claims=[
            EditorialClaim(
                type="hecho",
                text="Hecho",
                evidence_ids=["NEWS-1"],
            )
        ],
        sources_used=["NEWS-1"],
        pending_checks=[],
    )
    try:
        _quality_for_mode("digital", draft, package())
    except ValueError as exc:
        assert "máximo 80" in str(exc)
    else:
        raise AssertionError("Debió rechazar copy >80 palabras")


def test_cache_uses_evidence_fingerprint(tmp_path: Path):
    result = GeneratedEditorial(
        mode="brief",
        draft={"proposed_title": "X"},
        rendered_text="X",
        quality={"citation_coverage": 1.0},
        provider="gemini",
        model="test",
        attempts=1,
        generation_rounds=1,
    )
    path = save_cache(tmp_path, package(), result)
    assert path.exists()
    cached = load_cache(tmp_path, package(), "brief")
    assert cached is not None
    assert cached["text"] == "X"
    assert cache_path(tmp_path, package(), "brief") == path
