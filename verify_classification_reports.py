#!/usr/bin/env python3
"""Check completeness of the archived six-trick classification evidence.

This is a manifest/coverage audit, not a substitute for rerunning Z3.
"""
from pathlib import Path
import collections, hashlib, json

ROOT = Path(__file__).parent
V = ROOT / 'verification'
PARTS = [(1, 4000, 'sat_0001_4000.json'),
         (4001, 8000, 'sat_4001_8000.json'),
         (8001, 12000, 'sat_8001_12000.json'),
         (12001, 16000, 'sat_12001_16000.json'),
         (16001, 20000, 'sat_16001_20000.json'),
         (20001, 21407, 'sat_20001_21407.json')]
EXPECTED = {'111110': 199, '111100': 2361, '111010': 2121,
            '111000': 5286, '110110': 2489, '110100': 4293,
            '101010': 4658}


def main():
    data = (ROOT / 'skeleton6.tsv').read_bytes()
    lines = data.decode('ascii').splitlines()
    assert len(lines) == 21407
    counts = dict(collections.Counter(line.split()[1] for line in lines))
    assert counts == EXPECTED, counts
    all_satisfiable = []
    for start, stop, filename in PARTS:
        row = json.loads((V / filename).read_text())
        assert row['count'] == stop
        assert row['sat_cases'] == len(row['cases'])
        for item in row['cases']:
            assert start <= item['index'] <= stop
            assert item['line'] == lines[item['index'] - 1]
            all_satisfiable.append(item)
    assert all_satisfiable == [{
        'index': 2674,
        'line': '9 111010 2 2 1 5 1 1 6 7 8 2 12 3 13 4 5 15 0 9 1 10 11 14',
    }]
    for winner, count in EXPECTED.items():
        cert = json.loads((V / f'crosscheck_{winner}.json').read_text())
        assert cert['winner_word'] == winner
        assert cert['sets_identical'] is True
        assert cert['python_count'] == cert['cpp_count'] == count
    model = json.loads((V / 'six_classification_models.json').read_text())
    assert model['number_of_rank_and_gap_solutions'] == 1
    assert model['blocked_second_model_unsat'] is True
    assert model['feasible_skeleton_index'] == 2674
    backward = json.loads((V / 'basin_recheck.json').read_text())
    assert backward['backward_component_size'] == 181
    assert backward['balanced_states'] == 19
    summary = {
        'face_skeletons': len(lines),
        'rank_colorings_represented': 2688096,
        'skeleton_counts_by_winner': counts,
        'satisfiable_skeletons': all_satisfiable,
        'number_of_six_trick_equivalence_classes': 1,
        'oriented_orbits_with_named_players': 2,
        'distinct_periodic_rank_states': 12,
        'card_plays_per_period': 38,
        'balanced_backward_states_per_orbit': 19,
        'all_exact_python_cpp_crosschecks_passed': True,
        'skeleton_sha256': hashlib.sha256(data).hexdigest(),
        'native_z3_version': '4.13.3.0',
        'proof_status': 'exhaustive computer-assisted classification; not formally verified',
    }
    (V / 'six_classification_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('PASS:', json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
