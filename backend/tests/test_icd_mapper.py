from utils.icd_mapper import map_to_icd10

UNMATCHED_CODE = "Z03.89"


def test_exact_match_returns_expected_code():
    result = map_to_icd10("Type 2 diabetes mellitus")
    assert result["icd10_code"].startswith("E11")
    assert result["matched"] is True
    assert result["match_type"] == "exact"


def test_match_is_case_insensitive():
    lower = map_to_icd10("type 2 diabetes mellitus")
    upper = map_to_icd10("TYPE 2 DIABETES MELLITUS")
    assert lower["icd10_code"] == upper["icd10_code"]


def test_unmatched_falls_back_to_placeholder():
    result = map_to_icd10("qwerty zxcvb plover")
    assert result["icd10_code"] == UNMATCHED_CODE
    assert result["match_type"] == "unmatched"
    assert "warning" in result


def test_empty_string_is_unmatched():
    assert map_to_icd10("")["icd10_code"] == UNMATCHED_CODE


def test_result_always_has_contract_keys():
    for query in ["Type 2 diabetes mellitus", "", "xkcd9000 floopadoop"]:
        result = map_to_icd10(query)
        assert {"icd10_code", "icd10_description", "match_type"} <= result.keys()
