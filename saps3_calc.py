#!/usr/bin/env python3
"""SAPS 3 global model: hospital-mortality probability from a *precomputed* score.

Moreno et al. Intensive Care Med 2005;31:1345-1355.
DOI: 10.1007/s00134-005-2763-5

This module does NOT calculate the 20-variable SAPS 3 admission score.
It must not be used to determine treatment or individual prognosis.
"""

import argparse
import csv
import json
import math
import os
import tempfile
from typing import Any


MODEL_ID = "SAPS3-2005-global"
SOURCE_DOI = "10.1007/s00134-005-2763-5"


def _validate_score(value: Any) -> int:
    """Require a finite, integral published SAPS 3 score (theoretical range 0–217)."""
    if isinstance(value, bool):
        raise ValueError("SAPS 3 score must be an integer between 0 and 217")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("SAPS 3 score must be an integer between 0 and 217") from exc
    if not math.isfinite(number) or not number.is_integer() or not 0 <= number <= 217:
        raise ValueError("SAPS 3 score must be an integer between 0 and 217")
    return int(number)


def mortality_probability(saps3_score: Any) -> float:
    """Return probability of *in-hospital* death using the published global equation."""
    score = _validate_score(saps3_score)
    logit = -32.6659 + 7.3068 * math.log(score + 20.5958)
    # Numerically stable logistic function.
    if logit >= 0:
        return 1.0 / (1.0 + math.exp(-logit))
    exponential = math.exp(logit)
    return exponential / (1.0 + exponential)


def calculate_metrics(*, saps3_score: Any) -> dict[str, Any]:
    """Convert an existing SAPS 3 admission score; no unvalidated triage categories."""
    score = _validate_score(saps3_score)
    probability = mortality_probability(score)
    return {
        "saps3_score": score,
        "predicted_hospital_mortality": probability,
        "predicted_hospital_mortality_percent": round(probability * 100, 2),
        "model": MODEL_ID,
        "outcome": "In-hospital mortality",
    }


def process_batch(input_csv: str, output_csv: str) -> int:
    """Process CSV with column 'saps3_score'; preserve other columns locally."""
    source = os.path.realpath(os.path.abspath(input_csv))
    target = os.path.realpath(os.path.abspath(output_csv))
    if source == target:
        raise ValueError("Input and output CSV must be different files")
    if not os.path.isfile(source):
        raise FileNotFoundError(f"Input CSV not found: {source}")

    with open(source, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if not fields or "saps3_score" not in fields:
            raise ValueError("Input CSV must contain a 'saps3_score' header")
        if len(fields) != len(set(fields)):
            raise ValueError("Input CSV contains duplicate column headers")
        results = []
        for index, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV at line {index}")
            try:
                result = calculate_metrics(saps3_score=row["saps3_score"])
            except ValueError as exc:
                raise ValueError(f"CSV line {index}: {exc}") from exc
            row["predicted_hospital_mortality"] = f'{result["predicted_hospital_mortality"]:.8f}'
            row["predicted_hospital_mortality_percent"] = f'{result["predicted_hospital_mortality_percent"]:.2f}'
            results.append(row)

    output_fields = list(fields)
    for name in ("predicted_hospital_mortality", "predicted_hospital_mortality_percent"):
        if name not in output_fields:
            output_fields.append(name)
    output_dir = os.path.dirname(target)
    os.makedirs(output_dir, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=output_dir,
            prefix=".saps3-", suffix=".csv", delete=False
        ) as handle:
            temp_path = handle.name
            writer = csv.DictWriter(handle, fieldnames=output_fields)
            writer.writeheader()
            writer.writerows(results)
        os.replace(temp_path, target)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
    return len(results)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Estimate in-hospital mortality from an already calculated SAPS 3 score"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Calculate the global-model probability")
    single.add_argument("--score", required=True, help="Integer SAPS 3 score, 0 to 217")
    batch = commands.add_parser("batch", help="Convert a CSV containing 'saps3_score'")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            print(json.dumps(calculate_metrics(saps3_score=args.score), indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} records -> {args.output}")
    except (ValueError, FileNotFoundError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
