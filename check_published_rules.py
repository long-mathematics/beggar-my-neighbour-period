#!/usr/bin/env python3
"""Regression against Casella et al., American Mathematical Monthly 132 (2025),
978--994, DOI: 10.1080/00029890.2025.2558484.

The pile is appended oldest-played first, corresponding to turning the
face-up table pile over and placing it beneath the winner's face-down hand.
"""
import argparse
import json
from collections import Counter, deque
from pathlib import Path

PENALTY = {'J': 1, 'Q': 2, 'K': 3, 'A': 4}
A = '---K---Q-KQAJ-----AAJ--J--'
B = '----------Q----KQ-J-----KA'


def check():
    h = [deque(A.replace('-', 'C')), deque(B.replace('-', 'C'))]
    assert tuple(map(len, h)) == (26, 26)
    assert Counter(h[0] + h[1]) == {'C': 36, 'J': 4, 'Q': 4, 'K': 4, 'A': 4}
    leader = tricks = moves = 0
    seen = {}
    while True:
        state = (tuple(h[0]), tuple(h[1]), leader)
        if state in seen:
            start, start_moves = seen[state]
            result = {
                'transient_tricks': start,
                'primitive_cycle_tricks': tricks - start,
                'tricks_to_first_repeat': tricks,
                'plays_to_first_repeat': moves,
                'plays_inside_cycle': moves - start_moves,
            }
            assert result == {
                'transient_tricks': 4,
                'primitive_cycle_tricks': 62,
                'tricks_to_first_repeat': 66,
                'plays_to_first_repeat': 474,
                'plays_inside_cycle': 440,
            }, result
            return result
        seen[state] = tricks, moves
        player, claimant, debt, pile = leader, None, 0, []
        while True:
            if not h[player]:
                raise AssertionError('Published reference game terminated')
            card = h[player].popleft()
            pile.append(card)
            moves += 1
            if card in PENALTY:
                claimant, debt = player, PENALTY[card]
                player = 1 - player
            elif debt:
                debt -= 1
                if debt == 0:
                    h[claimant].extend(pile)
                    leader = claimant
                    break
            else:
                player = 1 - player
        tricks += 1
        assert tricks <= 10000


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    output = check()
    print(json.dumps(output, indent=2))
    if args.json:
        args.json.write_text(json.dumps(output, indent=2) + '\n')
