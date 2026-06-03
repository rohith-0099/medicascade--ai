from schemas import CaseFacts, Fact, Provenance


def test_fact_carries_optional_provenance():
    fact = Fact(
        label="glucose",
        value=180,
        unit="mg/dL",
        provenance=Provenance(pdf_id="p1", page=2, text_span="Glucose 180"),
    )
    assert fact.provenance.page == 2
    assert fact.unit == "mg/dL"


def test_casefacts_defaults_to_empty_lists():
    facts = CaseFacts()
    assert facts.labs == []
    assert facts.demographics == []
    assert facts.images == []


def test_casefacts_json_roundtrip():
    facts = CaseFacts(labs=[Fact(label="hba1c", value=9.1, unit="%")])
    dumped = facts.model_dump(mode="json")
    restored = CaseFacts(**dumped)
    assert restored.labs[0].label == "hba1c"
    assert restored.labs[0].value == 9.1
