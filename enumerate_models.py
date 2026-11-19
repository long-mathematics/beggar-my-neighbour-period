#!/usr/bin/env python3
"""Exhaust all ordinary-gap and rank models of the unique six-trick skeleton.

Produces one explicit model and a single blocking-clause UNSAT check. This
verifies uniqueness of the eighteen integer gaps and all rank assignments.
The standard-library check_rigidity.py provides a separate rational proof of
the same itinerary's uniqueness (even with unbounded ordinary-card count).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

import classify_six as cls
import native_z3_check as nat
import prove_minimum as pm


def enumerate_models(case, backend, max_models=1000):
    solver = pm.gap_problem(case, ordinary_count=36)
    variables = ([f'gap_{i}' for i in range(18)] +
                 [f'rank_{i}' for i in range(len(case['permutation_cycles']))])
    original = solver.smt()
    assert original.endswith('(check-sat)\n')
    prefix = original[:-len('(check-sat)\n')]
    blocks, solutions = [], []
    for _ in range(max_models):
        command = prefix + '\n'.join(blocks) + '\n(check-sat)\n'
        status = backend.check(command)
        if status == 'unsat':
            return solutions
        if status != 'sat':
            raise RuntimeError(f'Z3 returned {status!r}')
        values = backend.check(command + '(get-value (' + ' '.join(variables) + '))\n')
        pairs = re.findall(r'\((gap_\d+|rank_\d+)\s+(\d+)\)', values)
        assert len(pairs) == len(variables), values
        model = {key: int(value) for key, value in pairs}
        assert set(model) == set(variables)
        solutions.append(model)
        blocks.append('(assert (not (and ' +
                      ' '.join(f'(= {v} {model[v]})' for v in variables) + ')))')
    raise RuntimeError(f'Model cap {max_models} reached: cannot establish uniqueness')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).with_name('skeleton6.tsv'))
    parser.add_argument('--json', type=Path, default=Path(__file__).parent / 'verification/six_classification_models.json')
    parser.add_argument('--lib', default='libz3.so.4')
    args = parser.parse_args()
    lines = args.input.read_text().splitlines()
    assert len(lines) == cls.EXPECTED_TOTAL
    case = cls.case_from(lines[cls.EXPECTED_SAT_INDEX - 1])
    assert lines[cls.EXPECTED_SAT_INDEX - 1] == cls.EXPECTED_SAT_LINE
    backend = nat.NativeLib(args.lib)
    solutions = enumerate_models(case, backend)
    assert len(solutions) == 1, f'Expected unique solution, found {len(solutions)}'
    model = solutions[0]
    face_ranks = [0] * 16
    for i, orbit in enumerate(case['permutation_cycles']):
        for face in orbit:
            face_ranks[face] = model[f'rank_{i}']
    gaps = [model[f'gap_{i}'] for i in range(18)]
    assert sum(gaps) == 36
    a = case['A_face_count']

    def construct(ids, gs):
        return ''.join('C' * gs[i] + pm.RANK_SYMBOL[face_ranks[v]]
                       for i, v in enumerate(ids)) + 'C' * gs[-1]

    hand_a = construct(range(a), gaps[:a + 1])
    hand_b = construct(range(a, 16), gaps[a + 1:])
    witness = pm.verify_witness()
    assert hand_a == witness['A'] and hand_b == witness['B']
    assert tuple(case['winners']) == (1, 1, 1, 0, 1, 0)
    result = {
        'feasible_skeleton_index': cls.EXPECTED_SAT_INDEX,
        'number_of_rank_and_gap_solutions': 1,
        'blocked_second_model_unsat': True,
        'unique_hands': {'A': hand_a, 'B': hand_b, 'leader': 'A'},
        'face_permutation_orbits': case['permutation_cycles'],
        'model': model,
        'native_z3_version': backend.version,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: unique six-trick solution; second model UNSAT; matches 38-play witness')


if __name__ == '__main__':
    main()
