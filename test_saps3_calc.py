"""Regression tests against Moreno et al. 2005 SAPS 3 global model."""

import csv
import math

import pytest

from saps3_calc import calculate_metrics, mortality_probability, process_batch, main


@pytest.mark.parametrize(("score", "expected"), [
    (0, 0.0000258753719683624),
    (16, 0.0017230994),
    (35, 0.0353525914),
    (50, 0.1734936164),
    (60, 0.3559257142),
    (70, 0.5650101284),
    (100, 0.9130560145),
    (217, 0.9993292664),
])
def test_published_global_equation(score, expected):
    assert mortality_probability(score) == pytest.approx(expected, rel=2e-7)


def test_calculate_metrics_fields_and_outcome():
    result = calculate_metrics(saps3_score=50)
    assert result["saps3_score"] == 50
    assert result["predicted_hospital_mortality_percent"] == 17.35
    assert result["model"] == "SAPS3-2005-global"
    assert result["outcome"] == "In-hospital mortality"
    assert "clinical_recommendation" not in result


@pytest.mark.parametrize("invalid", [
    -1, 218, 50.5, "not a score", "", None, True, float("nan"),
    float("inf"), -float("inf"), 1e50,
])
def test_rejects_invalid_scores(invalid):
    with pytest.raises(ValueError, match="integer between 0 and 217"):
        mortality_probability(invalid)


def test_score_probability_is_monotonic():
    probabilities = [mortality_probability(i) for i in range(218)]
    assert all(0 < p < 1 for p in probabilities)
    assert probabilities == sorted(probabilities)


def test_batch_preserves_columns_and_rows(tmp_path):
    source = tmp_path / "source.csv"
    target = tmp_path / "nested" / "results.csv"
    source.write_text("case_id,saps3_score\nA,50\nB,60\n", encoding="utf-8")
    assert process_batch(str(source), str(target)) == 2
    with target.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["case_id"] for r in rows] == ["A", "B"]
    assert rows[0]["predicted_hospital_mortality_percent"] == "17.35"
    assert rows[1]["predicted_hospital_mortality_percent"] == "35.59"


def test_batch_rejects_missing_column(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("v1,v2\n10,20\n")
    with pytest.raises(ValueError, match="saps3_score"):
        process_batch(str(source), str(tmp_path / "output.csv"))


def test_batch_rejects_invalid_score_without_partial_overwrite(tmp_path):
    source = tmp_path / "bad.csv"
    target = tmp_path / "existing.csv"
    source.write_text("saps3_score\n50\nNaN\n", encoding="utf-8")
    target.write_text("untouched", encoding="utf-8")
    with pytest.raises(ValueError, match="line 3"):
        process_batch(str(source), str(target))
    assert target.read_text(encoding="utf-8") == "untouched"


def test_batch_rejects_same_input_output(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("saps3_score\n50\n")
    with pytest.raises(ValueError, match="different files"):
        process_batch(str(source), str(source))


def test_batch_rejects_duplicate_headers_and_malformed_rows(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("saps3_score,saps3_score\n50,60\n")
    with pytest.raises(ValueError, match="duplicate"):
        process_batch(str(source), str(tmp_path / "output.csv"))
    source.write_text("saps3_score,case\n50\n")
    with pytest.raises(ValueError, match="Malformed"):
        process_batch(str(source), str(tmp_path / "output.csv"))


def test_cli_single_and_invalid(capsys):
    assert main(["single", "--score", "50"]) == 0
    assert '"predicted_hospital_mortality_percent": 17.35' in capsys.readouterr().out
    with pytest.raises(SystemExit) as exit_info:
        main(["single", "--score", "NaN"])
    assert exit_info.value.code == 2
