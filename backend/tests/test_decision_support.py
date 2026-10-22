from app.services.exploration import decision_support


def test_business_profile_requires_human_review():
    item = {"evidence_package": {"evidence_state": "parcial", "independent_provenances": 1,
                                  "missing_information": ["Fuente primaria"], "contradictions": []}}
    result = decision_support(item, "business")
    assert result["profile"] == "business"
    assert result["requires_human_approval"] is True
    assert result["options"][0]["type"] == "verification"
    assert "probabilidad" in result["limitations"][0]


def test_editorial_mode_preserved():
    result = decision_support({"evidence_package": {}}, "editorial")
    assert "editorial" in result["options"][1]["action"]
    assert result["requires_human_approval"]


def test_research_profile_does_not_claim_verified_impact():
    result = decision_support({"evidence_package": {
        "evidence_state": "suficiente", "independent_provenances": 2,
        "missing_information": [], "contradictions": [],
    }}, "research")
    assert "análisis sectorial" in result["recommended_next_step"]
    assert result["assessment"].startswith("Evidencia preliminar")
