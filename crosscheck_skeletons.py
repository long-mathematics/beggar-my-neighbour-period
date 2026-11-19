#!/usr/bin/env python3
"""Compare independent Python and C++ six-trick face enumerations exactly.

Usage: python3 crosscheck_skeletons.py --winner 111110
Repeat for all seven canonical binary winner words (see README).
"""
from pathlib import Path
import sys
import json
import time
import argparse

import native_z3_check as nat
sys.modules['z3'] = nat.shim
import prove_minimum as pm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--winner', type=str, required=True)
    parser.add_argument('--json', type=Path)
    parser.add_argument('--input', type=Path, default=Path(__file__).with_name('skeleton6.tsv'))
    args = parser.parse_args()
    orig = pm.winner_patterns
    word = tuple(int(x) for x in args.winner)
    assert len(word) == 6 and word in orig(6)
    pm.winner_patterns = lambda p: [word] if p == 6 else orig(p)
    cpp = set()
    for line in args.input.read_text().splitlines():
        f = line.split()
        if f[1] != args.winner:
            continue
        key = (int(f[0]), tuple(map(int, f[2:8])), tuple(map(int, f[8:])))
        assert key not in cpp
        cpp.add(key)
    t0 = time.perf_counter()
    python = set()
    for case in pm.skeletons(6):
        key = (case['A_face_count'], tuple(case['pile_face_counts']),
               tuple(case['output_slot_to_input_id']))
        assert key not in python
        python.add(key)
    if python != cpp:
        raise RuntimeError({'python': len(python), 'cpp': len(cpp),
                            'python_only': list(python - cpp)[:5],
                            'cpp_only': list(cpp - python)[:5]})
    result = {'winner_word': args.winner, 'python_count': len(python),
              'cpp_count': len(cpp), 'sets_identical': True,
              'seconds': round(time.perf_counter() - t0, 3)}
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS:', json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
