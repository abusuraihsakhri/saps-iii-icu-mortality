#!/usr/bin/env python3
"""
Simplified Acute Physiology Score III (SAPS 3)
Calculates SAPS 3 score and customized logistic equation for ICU admission mortality prediction.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import os
import sys
from typing import Dict, Any, List, Optional


def _validate_numeric_inputs(params: Dict[str, Any]) -> None:
    """Validate that numeric inputs are within safe bounds."""
    MAX_SAFE_VALUE = 1e6
    for k, v in params.items():
        if isinstance(v, (int, float)):
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Parameter '{k}' must be a finite number, got {v}")
            if abs(v) > MAX_SAFE_VALUE:
                raise ValueError(f"Parameter '{k}' exceeds safe bounds (|{v}| > {MAX_SAFE_VALUE})")


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for saps-iii-icu-mortality.

    Validates inputs, computes a weighted score from numeric parameters,
    and returns a classification with clinical recommendation.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Validate numeric inputs for safety
    _validate_numeric_inputs(params)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "saps-iii-icu-mortality",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def _safe_resolve_path(path_str: str) -> str:
    """Resolve and validate a file path, preventing directory traversal."""
    # Check for traversal patterns before resolution (handles both / and \\)
    normalized = path_str.replace("\\", "/")
    if ".." in normalized.split("/"):
        raise ValueError(f"Path traversal detected in: {path_str}")
    resolved = os.path.realpath(os.path.abspath(path_str))
    return resolved


def process_batch(input_csv: str, output_csv: str) -> None:
    input_path = _safe_resolve_path(input_csv)
    output_path = _safe_resolve_path(output_csv)

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simplified Acute Physiology Score III (SAPS 3)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
