#!/usr/bin/env python3
"""Exact feasibility classification of standard-deck six-trick rank cycles.

Prerequisites:
    c++ -O3 -std=c++17 skeleton6.cpp -o skeleton6
    ./skeleton6 skeleton6.tsv

Uses libz3.so.4 directly via native_z3_check.py (Python bindings not needed).
Every generated face-only skeleton is reconstructed and checked, then its
complete eighteen-gap integer constraint system is solved. Unexpected solver
results fail closed. The optional --start/--stop partition the calculation.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import sys
import time

import native_z3_check as native
sys.modules['z3'] = native.shim
import prove_minimum as pm

EXPECTED_TOTAL = 21407
EXPECTED_SAT_INDEX = 2674
EXPECTED_SAT_LINE = '9 111010 2 2 1 5 1 1 6 7 8 2 12 3 13 4 5 15 0 9 1 10 11 14'


def case_from(line: str):
    words = line.split()
    assert len(words) == 24
    a = int(words[0])
    winners = tuple(int(d) for d in words[1])
    counts = tuple(int(x) for x in words[2:8])
    perm = tuple(int(x) for x in words[8:])
    assert 1 <= a < 16 and len(winners) == len(counts) == 6
    assert sorted(perm) == list(range(16))
    assert winners[-1] == 0
    hands = [deque(range(a)), deque(range(a, 16))]
    itinerary = []
    for winner, m in zip(winners, counts):
        events, packet = [], []
        for j in range(m):
            player = winner ^ ((m - 1 - j) & 1)
            label = hands[player].popleft()
            events.append((player, label))
            packet.append(label)
        hands[winner].extend(packet)
        itinerary.append(events)
    assert tuple(hands[0]) + tuple(hands[1]) == perm
    return {
        'A_face_count': a,
        'winners': winners,
        'pile_face_counts': counts,
        'face_events': itinerary,
        'output_slot_to_input_id': perm,
        'permutation_cycles': pm.permutation_cycles(perm),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).with_name('skeleton6.tsv'))
    parser.add_argument('--start', type=int, default=1, help='First skeleton index (one-based, inclusive)')
    parser.add_argument('--stop', '--limit', type=int, default=EXPECTED_TOTAL, help='Last skeleton index (inclusive)')
    parser.add_argument('--json', type=Path)
    parser.add_argument('--lib', default='libz3.so.4')
    args = parser.parse_args()
    assert 1 <= args.start <= args.stop <= EXPECTED_TOTAL
    native.backend = native.NativeLib(args.lib)
    data = args.input.read_bytes()
    count = 0
    sat = []
    by_winner = Counter()
    started = time.perf_counter()
    for index, line in enumerate(data.decode('ascii').splitlines(), 1):
        count = index
        if index < args.start:
            continue
        if index > args.stop:
            break
        case = case_from(line)
        status = pm.gap_problem(case, ordinary_count=36).check()
        if status not in ('sat', 'unsat'):
            raise RuntimeError(f'Solver returned {status!r} at skeleton {index}')
        if status == 'sat':
            sat.append({'index': index, 'line': line})
            by_winner[''.join(map(str, case['winners']))] += 1
            print(f'SAT skeleton {index}: {line}', flush=True)
        if index % 1000 == 0:
            print(f'Checked {index}: {len(sat)} SAT in selected range', flush=True)
    assert args.stop <= count
    if args.start == 1 and args.stop == EXPECTED_TOTAL:
        assert len(data.splitlines()) == EXPECTED_TOTAL
        assert sat == [{'index': EXPECTED_SAT_INDEX, 'line': EXPECTED_SAT_LINE}]
    result = {
        'range': [args.start, args.stop],
        'tested_skeletons': args.stop - args.start + 1,
        'sat_skeletons': sat,
        'sat_count': len(sat),
        'sat_by_winner_word': dict(by_winner),
        'skeleton_file_sha256': hashlib.sha256(data).hexdigest(),
        'native_z3_version': native.backend.version,
        'elapsed_seconds': round(time.perf_counter() - started, 3),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS:', json.dumps({k: v for k, v in result.items() if k != 'sat_skeletons'}), flush=True)


if __name__ == '__main__':
    main()
