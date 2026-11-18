#!/usr/bin/env python3
"""Check rigidity of a six-trick Beggar-My-Neighbour face itinerary.

Python standard library only. No input files, solver, network, or package
installation is required. Run:

    python3 check_rigidity.py
    python3 check_rigidity.py --json certificate.json
    python3 check_rigidity.py --json                 # JSON on standard output

Rules: queue tops are on the left, J/Q/K/A have penalties 1/2/3/4,
chronological pickup, winner leads. Ordinary cards are denoted C. A player
loses if required to play from an empty hand; a last card may win a pile.
The claimed period concerns ranks with all ordinary cards identified.

The initial face queues are
    player A: x y z z y z x y z
    player B: w x w y x w w.
The physical-face return permutation has four cycles of length four, so
(x,y,z,w) ranges over the 24 permutations of (1,2,3,4).

There are 18 ordinary gaps: a0,...,a9 and b0,...,b7. The return equations
have rank 17. Their sole free gap is u=b6. The formulas below parameterize
all their solutions; this is checked by exact rational row reduction and
substitution. In particular,
    a0 = (5u - 5w + 2x - 2y - 8z + 3)/12.
The second trick requires a0<y: after y is played, the other player's
ordinary gap before its interrupting x equals a0, using the return equations.
Consequently
    5u < 5w - 2x + 14y + 8z - 3 <= 85.
The maximum 85 is checked over all rank permutations below. As u is a
nonnegative integer, it suffices to check u=0,...,16. No total ordinary-card
count is imposed anywhere in this search.

Among the 24*17 possibilities, 21 have nonnegative integral gaps. Direct
play with physical face labels accepts precisely one: (K,A,Q,J), u=4,
with 36 ordinary cards. The scope of uniqueness is this face itinerary,
not every possible six-trick cycle.
"""

import argparse
from collections import Counter, deque
from fractions import Fraction as F
from itertools import permutations
import json
from pathlib import Path

# Face IDs 0,...,8 start in A; IDs 9,...,15 start in B.
RANK_ORBITS = ((0, 6, 13, 10), (1, 7, 4, 12),
               (2, 8, 5, 3), (9, 15, 14, 11))
WINNERS = (1, 1, 1, 0, 1, 0)  # 0=A, 1=B
FACE_COUNTS = (2, 2, 1, 5, 1, 1)
FACE_EVENTS = (
    ((0, 0), (1, 9)),
    ((0, 1), (1, 10)),
    ((1, 11),),
    ((0, 2), (1, 12), (0, 3), (1, 13), (0, 4)),
    ((1, 14),),
    ((0, 5),),
)
SYMBOLS = "CJQKA"


def gap_values(u, x, y, z, w):
    """All 18 gaps, as exact Fractions, solving the return equalities."""
    a0 = F(5*u - 5*w + 2*x - 2*y - 8*z + 3, 12)
    a1 = a0 + 2*w - 1
    a2 = F(2*u + 4*w + 2*x + y - 2*z - 3, 3)
    a3 = F(5*u + 7*w + 2*x - 2*y - 2*z - 3, 6)
    b0 = F(2*u - 2*w - x + y - 2*z, 3)
    b1 = 2*a0 + w
    b2 = F(u - w - 2*x + 2*y - 1, 4)
    b3 = 2*a1 - w + 1
    b5 = F(u - w + 2*y - 1, 2)
    return [a0, a1, a2, a3, a1, a3, a0, a1, a2, F(z),
            b0, b1, b2, b3, a0, b5, F(u), F(w)]


def return_equations(gaps, ranks):
    """Return-gap differences, each of which must equal zero."""
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9 = gaps[:10]
    b0, b1, b2, b3, b4, b5, b6, b7 = gaps[10:]
    x, y, z, w = ranks
    return [
        -a0+a6,
        -a1+a7,
        -a2+a8,
        2*a2-a3+a9-2*b2-2*w-2*x+1,
        -a2-a4+b2+b3+w+x-1,
        a3-a5,
        -a6+b4,
        a4-a7,
        2*a5-a8-2*b5-2*w+3*y-1,
        -a9+z,
        -a5-b0+b5+b6+w-y-z,
        2*a0-b1+b7,
        -a0+b0-b2,
        2*a1-b3-w+1,
        -a1+b1-b4+w-1,
        2*b2-b5+x,
        2*b5-b6+w-2*y+1,
        -b7+w,
    ]


def verify_parameterization():
    """Check the coefficient rank and completeness of the gap formulas."""
    zero = [F(0)] * 18
    ranks = (0, 0, 0, 0)
    constant = return_equations(zero, ranks)
    columns = []
    for j in range(18):
        unit = zero[:]
        unit[j] = F(1)
        columns.append([v-c for v, c in
                        zip(return_equations(unit, ranks), constant)])
    matrix = [list(row) for row in zip(*columns)]
    pivots = []
    pivot_row = 0
    for col in range(18):
        selected = next((r for r in range(pivot_row, 18)
                         if matrix[r][col]), None)
        if selected is None:
            continue
        matrix[pivot_row], matrix[selected] = matrix[selected], matrix[pivot_row]
        divisor = matrix[pivot_row][col]
        matrix[pivot_row] = [v/divisor for v in matrix[pivot_row]]
        for r in range(18):
            if r != pivot_row and matrix[r][col]:
                scale = matrix[r][col]
                matrix[r] = [v-scale*w for v, w in
                             zip(matrix[r], matrix[pivot_row])]
        pivots.append(col)
        pivot_row += 1
    assert pivots == [j for j in range(18) if j != 16]
    # The formulas and equations are affine in u. Checking u=0 and u=1
    # establishes their identity for every u, for each rank permutation.
    for ranks in permutations((1, 2, 3, 4)):
        for u in (0, 1):
            gaps = gap_values(u, *ranks)
            assert gaps[16] == u
            assert not any(return_equations(gaps, ranks))
    return len(pivots)


def make_hands(gaps, ranks):
    """Cards are (penalty, physical_face_id); ordinary cards use ID None."""
    colors = [None] * 16
    for rank, cycle in zip(ranks, RANK_ORBITS):
        for face_id in cycle:
            colors[face_id] = rank
    assert Counter(colors) == {1: 4, 2: 4, 3: 4, 4: 4}
    hands = []
    for start, count, gs in ((0, 9, gaps[:10]), (9, 7, gaps[10:])):
        hand = deque()
        for i in range(count):
            hand.extend([(0, None)] * gs[i])
            hand.append((colors[start+i], start+i))
        hand.extend([(0, None)] * gs[-1])
        hands.append(hand)
    return hands


def state_key(hands, leader):
    return (tuple(rank for rank, _ in hands[0]),
            tuple(rank for rank, _ in hands[1]), leader)


def play_trick(hands, leader):
    """Play one trick in place; return None if a required hand is empty."""
    player = leader
    claimant = None
    remaining = 0
    pile = []
    face_events = []
    while True:
        if not hands[player]:
            return None
        card = hands[player].popleft()
        rank, face_id = card
        pile.append(card)
        if rank:
            face_events.append((player, face_id))
            claimant = player
            remaining = rank
            player = 1-player
        elif remaining:
            remaining -= 1
            if remaining == 0:
                hands[claimant].extend(pile)
                return claimant, tuple(face_events), len(pile)
        else:
            player = 1-player


def verify_candidate(gaps, ranks):
    hands = make_hands(gaps, ranks)
    initial = state_key(hands, 0)
    boundaries = []
    split_sizes = []
    pile_lengths = []
    leader = 0
    for trick_index in range(6):
        boundaries.append(state_key(hands, leader))
        split_sizes.append([len(hands[0]), len(hands[1])])
        result = play_trick(hands, leader)
        if result is None:
            return None
        winner, events, count = result
        if (winner != WINNERS[trick_index]
                or len(events) != FACE_COUNTS[trick_index]
                or events != FACE_EVENTS[trick_index]):
            return None
        pile_lengths.append(count)
        leader = winner
    if state_key(hands, leader) != initial or len(set(boundaries)) != 6:
        return None
    return {
        "ranks_xyzw": list(ranks),
        "rank_symbols_xyzw": [SYMBOLS[r] for r in ranks],
        "u": gaps[16],
        "ordinary_count": sum(gaps),
        "gaps_A": gaps[:10],
        "gaps_B": gaps[10:],
        "A": "".join(SYMBOLS[r] for r in initial[0]),
        "B": "".join(SYMBOLS[r] for r in initial[1]),
        "initial_leader": "A",
        "primitive_rank_period": 6,
        "individual_plays": sum(pile_lengths),
        "pile_lengths": pile_lengths,
        "boundary_splits": split_sizes,
    }


def check():
    return_rank = verify_parameterization()
    rank_assignments = list(permutations((1, 2, 3, 4)))
    maximum = max(5*w-2*x+14*y+8*z-3 for x, y, z, w in rank_assignments)
    assert maximum == 85
    u_bound = (maximum-1)//5  # strict integer inequality 5u<maximum
    assert u_bound == 16
    rows = []
    solutions = []
    integral_count = 0
    for ranks in rank_assignments:
        candidates = []
        for u in range(u_bound+1):
            gs = gap_values(u, *ranks)
            assert not any(return_equations(gs, ranks))
            if any(g < 0 or g.denominator != 1 for g in gs):
                continue
            gaps = list(map(int, gs))
            integral_count += 1
            solution = verify_candidate(gaps, ranks)
            candidates.append({"u": u, "ordinary_count": sum(gaps),
                               "legal_periodic_realization": solution is not None})
            if solution is not None:
                solutions.append(solution)
        rows.append({"ranks_xyzw": list(ranks),
                     "nonnegative_integral_candidates": candidates})
    assert integral_count == 21
    assert len(solutions) == 1
    only = solutions[0]
    assert only["ranks_xyzw"] == [3, 4, 2, 1]
    assert only["u"] == 4 and only["ordinary_count"] == 36
    assert only["individual_plays"] == 38
    return {
        "scope": "The specified six-trick face itinerary; ordinary count unrestricted",
        "return_equation_rank": return_rank,
        "free_gap": "b6",
        "u_bound_inclusive": u_bound,
        "rank_assignments": len(rank_assignments),
        "rational_cases_examined": len(rank_assignments)*(u_bound+1),
        "nonnegative_integral_candidates": integral_count,
        "legal_periodic_realizations": len(solutions),
        "winner_sequence": "BBBABA",
        "pile_face_counts": list(FACE_COUNTS),
        "rank_orbits": RANK_ORBITS,
        "results_by_rank_assignment": rows,
        "solutions": solutions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", nargs="?", const="-", metavar="PATH",
                        help="write full JSON certificate to PATH, or stdout if omitted")
    args = parser.parse_args()
    certificate = check()
    if args.json == "-":
        print(json.dumps(certificate, indent=2))
        return
    solution = certificate["solutions"][0]
    print("PASS: all 24 rank assignments and 17 parameter values checked (408 cases).")
    print("Return system rank 17; 21 nonnegative integral candidates; 1 legal realization.")
    print("Unique ranks (x,y,z,w)=(K,A,Q,J), u=4, ordinary cards=36.")
    print("Primitive rank period=6 tricks; individual plays=38; initial split=30/22.")
    print("A:", solution["A"])
    print("B:", solution["B"])
    if args.json:
        destination = Path(args.json)
        destination.write_text(json.dumps(certificate, indent=2)+"\n", encoding="utf-8")
        print("Certificate written to", destination)


if __name__ == "__main__":
    main()
