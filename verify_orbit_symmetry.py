#!/usr/bin/env python3
"""Audit both named-player orientations of the unique six-trick rank cycle.

No third-party dependencies. Computes both full backward components from
scratch, verifies player-swap conjugacy and component disjointness, and counts
all balanced ancestors, including the next-player-to-lead distinction.

This verifies the equality-case basin assertions for the displayed cycle. The
independent global classification of all six-trick cycles is handled by
skeleton6.cpp, classify_six.py and enumerate_models.py.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import json
from pathlib import Path

import backward_component as bm


def swap(state):
    """Exchange the two named hands and the next leader."""
    return state[1], state[0], state[2] ^ 1


def component(initial):
    """Find every rank state reaching the indicated primitive cycle."""
    cycle = []
    state = initial
    for _ in range(6):
        assert state not in cycle
        cycle.append(state)
        state = bm.trick(state)
        assert state is not None
    assert state == initial

    distance = {state: 0 for state in cycle}
    queue = deque(cycle)
    while queue:
        current = queue.popleft()
        for previous in bm.predecessors(current):
            assert bm.trick(previous) == current
            if previous not in distance:
                distance[previous] = distance[current] + 1
                queue.append(previous)
    return cycle, distance


def audit():
    first = (bm.dec(bm.A0), bm.dec(bm.B0), 0)
    cycle_a, basin_a = component(first)
    cycle_b, basin_b = component(swap(first))

    assert [swap(state) for state in cycle_a] == cycle_b
    assert {swap(state): depth for state, depth in basin_a.items()} == basin_b
    assert not set(basin_a).intersection(basin_b)
    assert len(cycle_a) == len(cycle_b) == 6
    assert len(basin_a) == len(basin_b) == 181
    assert max(basin_a.values()) == max(basin_b.values()) == 4

    inventory = Counter(first[0] + first[1])
    assert inventory == {0: 36, 1: 4, 2: 4, 3: 4, 4: 4}
    assert all(Counter(s[0] + s[1]) == inventory for s in basin_a | basin_b)
    assert all(bm.trick(swap(s)) == swap(bm.trick(s))
               for s in (basin_a | basin_b) if bm.trick(s) is not None)

    balanced = {s for s in basin_a | basin_b if len(s[0]) == 26}
    assert len(balanced) == 38
    assert sum(len(s[0]) == 26 for s in basin_a) == 19
    assert sum(len(s[0]) == 26 for s in basin_b) == 19
    assert all(len(s[0]) != 26 for s in cycle_a + cycle_b)
    by_leader = Counter('AB'[s[2]] for s in balanced)
    assert by_leader == {'A': 19, 'B': 19}

    result = {
        'primitive_period_tricks': 6,
        'cycles_up_to_player_exchange': 1,
        'oriented_cycles_with_named_players': 2,
        'periodic_boundary_states': 12,
        'backward_states_per_orientation': [len(basin_a), len(basin_b)],
        'backward_components_disjoint': True,
        'maximum_preperiod_per_orientation': [max(basin_a.values()), max(basin_b.values())],
        'balanced_ancestors_per_orientation': [19, 19],
        'balanced_ancestors_total': len(balanced),
        'balanced_ancestors_by_next_leader': dict(sorted(by_leader.items())),
        'player_swap_conjugacy_verified': True,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS:', json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
