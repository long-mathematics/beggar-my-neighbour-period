#!/usr/bin/env python3
"""Classify all standard-deck rank-state cycles using at most 38 card plays.

The exact gap model and both direct simulators are shared with prove_minimum.
Every satisfiable skeleton is exhausted by blocking all eighteen gaps and all
orbit-rank variables. Each resulting cycle is independently replayed and
canonicalized under cyclic phase and player exchange. UNKNOWN is fatal.

Verify the committed complete candidate archive:
    python3 verify_unique38.py --workers 2
Regenerate both independent candidate sets before the full classification:
    python3 verify_unique38.py --crosscheck --workers 2

Both players must win in a cycle. If p is its trick count and c its cyclic
winner-change count, then L >= 2*p+c and c >= 2. Thus L <= 38 forces p <= 18.
A one-trick cycle is impossible. The enumerators cover p=2,...,18 and every
nonempty initial face split; ordinary gaps are unrestricted apart from their
standard-deck total of 36.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

import prove_minimum as pm

z3 = pm.z3
ROOT = Path(__file__).resolve().parent
EXPECTED = {
    2: 2, 3: 10, 4: 145, 5: 565, 6: 4234, 7: 7119, 8: 13140,
    9: 8530, 10: 5178, 11: 3340, 12: 1340, 13: 166, 14: 35,
    15: 4, 16: 0, 17: 0, 18: 0,
}
INPUT_SHA256 = "24a95556f2412b46bfcda9dfa4cacb5061f9428b55441c74d92ef1464a8d6f7e"
KNOWN_SKELETON = "9 111010 2 2 1 5 1 1 6 7 8 2 12 3 13 4 5 15 0 9 1 10 11 14"
GENERATORS = ("bounded_play_skeletons.cpp", "independent_play_skeletons.cpp")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def case_from(line):
    """Reconstruct every labelled face event and validate its exact return."""
    fields = line.split()
    require(len(fields) >= 20, "Short candidate line")
    initial_a = int(fields[0])
    word = fields[1]
    require(set(word) == {"0", "1"}, "Winner word must contain both players")
    winners = tuple(map(int, word))
    period = len(winners)
    require(2 <= period <= 18 and len(fields) == 18 + period,
            "Bad candidate period or field count")
    require(winners[-1] == 0 and 1 <= initial_a <= 15,
            "Invalid initial leader/final winner or face split")
    counts = tuple(map(int, fields[2:2 + period]))
    permutation = tuple(map(int, fields[2 + period:]))
    require(all(1 <= count <= 15 for count in counts), "Bad face count")
    require(sorted(permutation) == list(range(16)), "Bad face permutation")
    cycles = pm.permutation_cycles(permutation)
    require(all(len(cycle) <= 4 for cycle in cycles), "Uncolorable face permutation")
    hands = [deque(range(initial_a)), deque(range(initial_a, 16))]
    itinerary = []
    for winner, count in zip(winners, counts):
        pile, events = [], []
        for j in range(count):
            player = winner ^ ((count - 1 - j) & 1)
            require(bool(hands[player]), "Face itinerary exhausts its required hand")
            face = hands[player].popleft()
            pile.append(face)
            events.append((player, face))
        hands[winner].extend(pile)
        require(bool(hands[0]) and bool(hands[1]), "A boundary hand has no face")
        itinerary.append(events)
    require(len(hands[0]) == initial_a, "Face-count balance fails")
    require(tuple(hands[0]) + tuple(hands[1]) == permutation,
            "Replayed face permutation differs from supplied permutation")
    return {
        "A_face_count": initial_a,
        "winners": winners,
        "pile_face_counts": counts,
        "face_events": itinerary,
        "output_slot_to_input_id": permutation,
        "permutation_cycles": cycles,
    }


def canonical_cycle(states):
    """Canonical complete boundary cycle under phase and player exchange."""
    variants = []
    for exchange in (False, True):
        transformed = []
        for hand_a, hand_b, leader in states:
            if exchange:
                hand_a, hand_b, leader = hand_b, hand_a, 1 - leader
            transformed.append((pm.encode(hand_a), pm.encode(hand_b), leader))
        for cut in range(len(states)):
            variants.append(tuple(transformed[cut:] + transformed[:cut]))
    return min(variants)


def decode_and_verify(case, model, details):
    """Decode a model and replay its full return with both shared simulators."""
    ranks = [model.eval(rank).as_long() for rank in details["ranks"]]
    gaps = [model.eval(gap).as_long() for gap in details["gaps"]]
    initial_a = case["A_face_count"]

    def construct(ids, hand_gaps):
        return "".join("C" * hand_gaps[i] + pm.RANK_SYMBOL[ranks[label]]
                       for i, label in enumerate(ids)) + "C" * hand_gaps[-1]

    hand_a = construct(range(initial_a), gaps[:initial_a + 1])
    hand_b = construct(range(initial_a, 16), gaps[initial_a + 1:])
    initial = (pm.decode(hand_a), pm.decode(hand_b), 0)
    require(Counter(initial[0] + initial[1]) == {0: 36, 1: 4, 2: 4, 3: 4, 4: 4},
            "Decoded model has wrong inventory")
    state, states, trace, first_return = initial, [], [], None
    for i, expected_winner in enumerate(case["winners"]):
        states.append(state)
        after, events = pm.trick(state)
        require((after, events) == pm.challenge_trick(state), "Reference simulators disagree")
        require(after is not None, "Decoded model terminates")
        require(after[2] == expected_winner, "Decoded winner differs from its skeleton")
        require(sum(card != 0 for _, card in events) == case["pile_face_counts"][i],
                "Decoded face count differs from its skeleton")
        trace.append({
            "winner": "AB"[after[2]],
            "pile": pm.encode(card for _, card in events),
            "plays": [["AB"[player], pm.RANK_SYMBOL[card]] for player, card in events],
            "A_before": pm.encode(state[0]), "B_before": pm.encode(state[1]),
            "leader": "AB"[state[2]],
            "A_after": pm.encode(after[0]), "B_after": pm.encode(after[1]),
        })
        state = after
        if state == initial and first_return is None:
            first_return = i + 1
    require(state == initial and first_return is not None, "Decoded model fails to return")
    total = sum(len(row["plays"]) for row in trace)
    require(total == model.eval(details["plays"]).as_long() and total <= 38,
            "Symbolic and actual play counts differ")
    primitive_plays = sum(len(row["plays"]) for row in trace[:first_return])
    return {
        "A": hand_a, "B": hand_b, "leader": "A",
        "period": len(case["winners"]), "plays": total,
        "primitive_period": first_return, "primitive_plays": primitive_plays,
        "gaps": gaps,
        "orbit_ranks": [model.eval(rank).as_long() for rank in details["orbit_ranks"]],
        "canonical_cycle": canonical_cycle(states[:first_return]),
        "trace": trace,
    }


def classify_batch(batch):
    counts, satisfiable = Counter(), []
    for index, line in batch:
        case = case_from(line)
        solver, details = pm.gap_problem(case, ordinary_count=36, play_budget=38,
                                         return_details=True)
        # These variables specify the entire initial rank state. Blocking only
        # ranks, only gaps, or only a derived play count would miss models.
        variables = details["gaps"] + details["orbit_ranks"]
        models = []
        while True:
            status = solver.check()
            if status == z3.unsat:
                break
            if status != z3.sat:
                raise RuntimeError(f"UNKNOWN at candidate {index}: {solver.reason_unknown()}")
            model = solver.model()
            decoded = decode_and_verify(case, model, details)
            decoded["bindings"] = {str(variable): model.eval(variable).as_long()
                                   for variable in variables}
            models.append(decoded)
            solver.add(z3.Or(*[variable != model.eval(variable) for variable in variables]))
        counts[len(case["winners"])] += 1
        if models:
            satisfiable.append({
                "index": index, "line": line, "models": models,
                "all_models_exhausted": True, "final_status": "unsat",
                "blocked_variables": len(variables),
            })
    return {"counts": dict(counts), "sat": satisfiable}


def read_archive(path):
    packed = path.read_bytes()
    raw = gzip.decompress(packed) if path.suffix == ".gz" else packed
    require(digest(raw) == INPUT_SHA256, "Candidate archive SHA-256 mismatch")
    lines = raw.decode("ascii").splitlines()
    require(len(lines) == len(set(lines)), "Duplicate candidate lines")
    counts = Counter(len(line.split()[1]) for line in lines)
    require(sum(counts.values()) == sum(EXPECTED.values()), "Wrong total candidate count")
    require(all(counts[period] == count for period, count in EXPECTED.items()),
            "Wrong per-period candidate counts")
    return lines, digest(raw), digest(packed)


def crosscheck_generators(lines, compiler):
    """Regenerate with both implementations and compare all candidate lines."""
    by_period = {period: set() for period in EXPECTED}
    for line in lines:
        by_period[len(line.split()[1])].add(line)
    records = []
    with tempfile.TemporaryDirectory(prefix="bmn-play-period-") as work:
        work = Path(work)
        for source in GENERATORS:
            executable = work / Path(source).stem
            command = shlex.split(compiler) + ["-O3", "-std=c++20", str(ROOT / source),
                                               "-o", str(executable)]
            subprocess.run(command, check=True, text=True, capture_output=True)
            for period in EXPECTED:
                output = work / f"{executable.name}-{period}.tsv"
                started = time.perf_counter()
                run = subprocess.run([str(executable), str(period), "38", str(output)],
                                     check=True, text=True, capture_output=True)
                generated = output.read_text().splitlines()
                require(len(generated) == len(set(generated)), "Generator emitted duplicates")
                require(set(generated) == by_period[period],
                        f"Generator candidate-set mismatch: {source}, p={period}")
                records.append({
                    "source": source, "period": period, "candidates": len(generated),
                    "same_set": True, "seconds": round(time.perf_counter() - started, 3),
                    "stderr": run.stderr,
                })
                print(f"MATCH {source}: p={period}, {len(generated):,} candidates", flush=True)
    return records


def validate_unique_result(satisfiable):
    """Verify the claimed conclusion only after every model has been exhausted."""
    models = [state for entry in satisfiable for state in entry["models"]]
    orbit_keys = {json.dumps(state["canonical_cycle"]) for state in models}
    require(len(satisfiable) == len(models) == len(orbit_keys) == 1,
            f"Uniqueness fails: {len(satisfiable)} SAT skeletons, {len(models)} models, {len(orbit_keys)} orbits")
    witness = models[0]
    known = pm.verify_witness()
    balanced = pm.verify_balanced_entry(known)
    require(satisfiable[0]["line"] == KNOWN_SKELETON, "Unexpected unique face skeleton")
    require((witness["A"], witness["B"]) == (known["A"], known["B"]),
            "Unique model differs from the known witness")
    require(witness["plays"] == witness["primitive_plays"] == 38,
            "A cycle with fewer than 38 plays was found")
    require(witness["period"] == witness["primitive_period"] == 6,
            "Unexpected primitive trick period")
    require(satisfiable[0]["all_models_exhausted"] and satisfiable[0]["final_status"] == "unsat",
            "SAT skeleton's models were not exhausted")
    orbits = [json.loads(key) for key in sorted(orbit_keys)]
    oriented = {tuple(state) for state in orbits[0]}
    exchanged = {(b, a, 1 - leader) for a, b, leader in oriented}
    require(len(oriented) == len(exchanged) == 6 and not (oriented & exchanged),
            "Unexpected player-exchange symmetry of the unique cycle")
    return orbits, balanced


def write_blocking_queries(entry, destination):
    """Save the unique SAT query and its complete 22-variable blocking query."""
    solver, details = pm.gap_problem(case_from(entry["line"]), ordinary_count=36,
                                     play_budget=38, return_details=True)
    variables = details["gaps"] + details["orbit_ranks"]
    bindings = entry["models"][0]["bindings"]
    require(set(bindings) == {str(variable) for variable in variables},
            "Blocking clause omitted a variable")
    positive = solver.sexpr() + "\n(check-sat)\n"
    solver.add(z3.Or(*[variable != bindings[str(variable)] for variable in variables]))
    blocked = solver.sexpr() + "\n(check-sat)\n"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "known_sat38.smt2").write_text(positive)
    (destination / "known_sat38_blocked.smt2").write_text(blocked)
    return {
        "blocked_variables": len(variables), "bindings": bindings,
        "positive_sha256": digest(positive.encode()), "positive_status": "sat",
        "blocked_sha256": digest(blocked.encode()), "blocked_status": entry["final_status"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", type=Path, default=ROOT / "play_candidates_le38.tsv.gz")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--crosscheck", action="store_true")
    parser.add_argument("--compiler", default=os.environ.get("CXX", "c++"))
    parser.add_argument("--json", type=Path, default=ROOT / "verification/play_period/classification.json")
    args = parser.parse_args()
    require(args.workers >= 1, "Workers must be positive")
    started = time.perf_counter()
    lines, raw_hash, file_hash = read_archive(args.candidates)
    generator_checks = crosscheck_generators(lines, args.compiler) if args.crosscheck else []
    indexed = list(enumerate(lines, 1))
    batches = [indexed[i:i + 100] for i in range(0, len(indexed), 100)]
    checked, satisfiable, last_progress = Counter(), [], 0
    solve_started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(classify_batch, batches):
            checked.update(result["counts"])
            satisfiable.extend(result["sat"])
            count = sum(checked.values())
            for entry in result["sat"]:
                print(f"SAT skeleton {entry['index']}: {len(entry['models'])} model(s), then UNSAT", flush=True)
            if count - last_progress >= 1000 or count == len(lines):
                print(f"CHECKED {count:,}/{len(lines):,}; SAT skeletons {len(satisfiable)}; "
                      f"{time.perf_counter() - solve_started:.1f}s", flush=True)
                last_progress = count
    require(all(checked[period] == count for period, count in EXPECTED.items())
            and sum(checked.values()) == len(lines), "Incomplete classification")
    orbits, balanced = validate_unique_result(satisfiable)
    blocking = write_blocking_queries(satisfiable[0], args.json.parent)
    sources = ["prove_minimum.py", "verify_unique38.py", *GENERATORS]
    report = {
        "theorem": "The unique standard-deck rank-state cycle using at most 38 plays, up to phase and player exchange, is the known six-trick 38-play cycle",
        "scope": {"ordinary_cards": 36, "each_face_rank": 4, "pickup": "chronological",
                  "next_leader": "winner", "initial_split": "any nonempty split",
                  "state": "both ordered rank queues and next leader"},
        "play_budget": 38, "period_range": [2, 18], "total_candidates": len(lines),
        "periods": [{"period": period, "candidates": count, "checked": checked[period]}
                    for period, count in EXPECTED.items()],
        "sat_skeleton_count": len(satisfiable),
        "model_count": sum(len(entry["models"]) for entry in satisfiable),
        "canonical_orbit_count": len(orbits), "canonical_orbits": orbits,
        "oriented_cycles": 2, "boundary_states_per_oriented_cycle": 6,
        "oriented_cycles_disjoint": True, "balanced_ancestor": balanced,
        "all_models_exhausted": True, "unknown": 0, "sat_skeletons": satisfiable,
        "blocking_certificate": blocking, "generator_crosschecks": generator_checks,
        "input_uncompressed_sha256": raw_hash, "input_file_sha256": file_hash,
        "source_sha256": {name: digest((ROOT / name).read_bytes()) for name in sources},
        "z3": z3.get_version_string(), "workers": args.workers,
        "solver_seconds": round(time.perf_counter() - solve_started, 3),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.json.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {len(lines):,} skeletons, one model, one orbit, 38 plays; report {args.json}", flush=True)


if __name__ == "__main__":
    main()
