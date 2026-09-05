import math
import pytest
from saps3_calc import calculate_metrics, process_batch


def test_saps3_calc_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_saps3_calc_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_classification_low():
    """Score below 10 should be classified as Low / Standard."""
    res = calculate_metrics(v1=5.0, v2=2.0)
    assert res["classification"] == "Low / Standard"
    assert res["clinical_recommendation"] == "Standard monitoring or negative cutoff"


def test_calculate_metrics_classification_moderate():
    """Score between 10 and 25 should be Moderate / Intermediate."""
    res = calculate_metrics(v1=15.0, v2=3.0)
    assert res["classification"] == "Moderate / Intermediate"


def test_calculate_metrics_classification_high():
    """Score >= 25 should be High / Severe."""
    res = calculate_metrics(v1=30.0, v2=5.0)
    assert res["classification"] == "High / Severe"
    assert "Urgent clinical intervention" in res["clinical_recommendation"]


def test_calculate_metrics_rejects_nan():
    """NaN values should raise ValueError."""
    with pytest.raises(ValueError, match="finite number"):
        calculate_metrics(v1=float("nan"))


def test_calculate_metrics_rejects_inf():
    """Infinite values should raise ValueError."""
    with pytest.raises(ValueError, match="finite number"):
        calculate_metrics(v1=float("inf"))


def test_calculate_metrics_rejects_extreme_values():
    """Values exceeding safe bounds should raise ValueError."""
    with pytest.raises(ValueError, match="exceeds safe bounds"):
        calculate_metrics(v1=1e10)


def test_process_batch_missing_input(tmp_path):
    """Missing input file should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))


def test_process_batch_path_traversal():
    """Path traversal attempts should be rejected."""
    with pytest.raises(ValueError, match="Path traversal"):
        process_batch("../etc/passwd", "out.csv")
