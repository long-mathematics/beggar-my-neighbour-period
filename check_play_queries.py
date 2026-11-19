#!/usr/bin/env python3
r"""Check the recorded 38-play SAT and complete blocking queries with native Z3.

This uses only Python's standard library and an installed Z3 shared library;
the Python z3-solver package is not required. Query hashes are checked against
the full classification report before either query is passed to the solver.
The check confirms the positive case and its complete second-model exclusion;
it does not rerun the global exclusion of the other 43,807 face skeletons.

    python3 check_play_queries.py \
        --json verification/play_period/native_query_check.json

After a fresh classification, select its matching report with --classification.
The two queries are read from that report's directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from native_z3_check import NativeLib


ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check(classification_path, library):
    report_bytes = classification_path.read_bytes()
    classification = json.loads(report_bytes)
    require(classification["play_budget"] == 38,
            "The classification report must use the 38-play bound")
    require(classification["sat_skeleton_count"] == 1
            and classification["model_count"] == 1
            and classification["all_models_exhausted"] is True,
            "The report must record one fully exhausted positive case")
    certificate = classification["blocking_certificate"]
    expected_variables = {f"gap_{i}" for i in range(18)} | {f"rank_{i}" for i in range(4)}
    require(certificate["blocked_variables"] == 22
            and set(certificate["bindings"]) == expected_variables,
            "The positive case must block all 18 gaps and all four orbit ranks")

    backend = NativeLib(library)
    queries = []
    for kind, name, expected in (
        ("positive", "known_sat38.smt2", "sat"),
        ("blocked", "known_sat38_blocked.smt2", "unsat"),
    ):
        query = (classification_path.parent / name).read_bytes()
        query_hash = hashlib.sha256(query).hexdigest()
        require(query_hash == certificate[f"{kind}_sha256"],
                f"Query hash differs from the classification report: {name}")
        status = backend.check(query.decode("ascii"))
        require(status == expected,
                f"Native Z3 returned {status!r}, expected {expected!r}, for {name}")
        queries.append({"file": name, "sha256": query_hash, "status": status})

    return {
        "scope": "Known 38-play positive case and its complete second-model exclusion",
        "global_exclusion_recomputed": False,
        "classification_file": classification_path.name,
        "classification_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "native_z3_version": backend.version,
        "blocked_variables": 22,
        "query_hashes_match_classification": True,
        "queries": queries,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--classification", type=Path,
                        default=ROOT / "verification/play_period/classification.json")
    parser.add_argument("--lib", default="libz3.so.4",
                        help="Installed native Z3 shared library name or path")
    parser.add_argument("--json", type=Path,
                        help="Also write the verification report to this file")
    args = parser.parse_args()
    result = check(args.classification, args.lib)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
