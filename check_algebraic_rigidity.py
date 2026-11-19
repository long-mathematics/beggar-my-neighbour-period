#!/usr/bin/env python3
"""Certify uniqueness within the surviving six-trick skeleton by arithmetic.

Standard library only. No SAT/SMT solver, numerical tolerance, external input,
or enumeration of 408 parameter cases is used. The global skeleton exclusion
is a separate computer-assisted calculation; this checks its positive case.

The gap formulas and stated equations are adapted from Christopher D. Long's
MIT-licensed beggar-my-neighbour-period/check_rigidity.py. They are independently
checked here against symbolic chronological FIFO transport. A new total-count
congruence makes the standard-inventory rigidity deduction especially short.
"""
from collections import Counter, deque
from fractions import Fraction as F
from pathlib import Path
import argparse
import json

NVAR = 22  # g0,...,g17, x,y,z,w; an additional coordinate is constant.
SYMBOLS = "CJQKA"
ORBIT_IDS = ((0, 6, 13, 10), (1, 7, 4, 12),
             (2, 8, 5, 3), (9, 15, 14, 11))
EVENTS = (((0, 0), (1, 9)), ((0, 1), (1, 10)), ((1, 11),),
          ((0, 2), (1, 12), (0, 3), (1, 13), (0, 4)),
          ((1, 14),), ((0, 5),))
WINNERS = (1, 1, 1, 0, 1, 0)


class Affine:
    """Exact rational affine forms, with no symbolic algebra dependency."""
    def __init__(self, coefficients):
        self.c = tuple(map(F, coefficients))
        assert len(self.c) == NVAR + 1

    @staticmethod
    def constant(value):
        return Affine([0] * NVAR + [value])

    @staticmethod
    def variable(index):
        return Affine([int(i == index) for i in range(NVAR + 1)])

    def __add__(self, other):
        other = other if isinstance(other, Affine) else self.constant(other)
        return Affine(a+b for a, b in zip(self.c, other.c))

    __radd__ = __add__

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + -other

    def __rsub__(self, other):
        return other + -self

    def __mul__(self, scalar):
        return Affine(a*F(scalar) for a in self.c)

    __rmul__ = __mul__

    def __truediv__(self, scalar):
        return self * (F(1)/scalar)

    def __eq__(self, other):
        other = other if isinstance(other, Affine) else self.constant(other)
        return self.c == other.c

    def substitute(self, variables):
        assert len(variables) == NVAR
        return self.c[-1] + sum(a*b for a, b in zip(self.c, variables))


def gap_formulas(u, x, y, z, w):
    a0 = (5*u-5*w+2*x-2*y-8*z+3)/12
    a1 = a0+2*w-1
    a2 = (2*u+4*w+2*x+y-2*z-3)/3
    a3 = (5*u+7*w+2*x-2*y-2*z-3)/6
    b0 = (2*u-2*w-x+y-2*z)/3
    b1 = 2*a0+w
    b2 = (u-w-2*x+2*y-1)/4
    b3 = 2*a1-w+1
    b5 = (u-w+2*y-1)/2
    return [a0, a1, a2, a3, a1, a3, a0, a1, a2, z,
            b0, b1, b2, b3, a0, b5, u, w]


def stated_equations(gs, ranks):
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9 = gs[:10]
    b0, b1, b2, b3, b4, b5, b6, b7 = gs[10:]
    x, y, z, w = ranks
    return [-a0+a6, -a1+a7, -a2+a8,
            2*a2-a3+a9-2*b2-2*w-2*x+1,
            -a2-a4+b2+b3+w+x-1, a3-a5, -a6+b4, a4-a7,
            2*a5-a8-2*b5-2*w+3*y-1, -a9+z,
            -a5-b0+b5+b6+w-y-z, 2*a0-b1+b7, -a0+b0-b2,
            2*a1-b3-w+1, -a1+b1-b4+w-1, 2*b2-b5+x,
            2*b5-b6+w-2*y+1, -b7+w]


def derive_return_equations(gs, rank_variables):
    """Derive all gap equations from face events, rather than hardcode them."""
    ranks = {f: r for r, orb in zip(rank_variables, ORBIT_IDS) for f in orb}
    faces = [list(range(9)), list(range(9, 16))]
    gaps = [list(gs[:10]), list(gs[10:])]
    leader = 0
    for trick_index, events in enumerate(EVENTS):
        first, face = events[0]
        assert faces[first][0] == face
        first_gap = gaps[first].pop(0)
        faces[first].pop(0)
        offset = int(first != leader)
        gaps[first ^ 1][0] -= first_gap+offset
        pile_faces, pile_gaps = [face], [2*first_gap+offset]
        winner = first
        for player, face in events[1:]:
            assert player == winner ^ 1 and faces[player][0] == face
            pile_faces.append(faces[player].pop(0))
            pile_gaps.append(gaps[player].pop(0))
            winner = player
        assert winner == WINNERS[trick_index]
        payment = ranks[pile_faces[-1]]
        gaps[winner ^ 1][0] -= payment
        gaps[winner][-1] += pile_gaps[0]
        gaps[winner].extend(pile_gaps[1:]+[payment])
        faces[winner].extend(pile_faces)
        leader = winner
    assert leader == 0 and [len(h) for h in faces] == [9, 7]
    permutation = faces[0]+faces[1]
    seen, orbits = set(), []
    for initial in range(16):
        if initial in seen:
            continue
        orbit, face = set(), initial
        while face not in seen:
            orbit.add(face)
            seen.add(face)
            face = permutation[face]
        orbits.append(frozenset(orbit))
    assert set(orbits) == {frozenset(orb) for orb in ORBIT_IDS}
    return [a-b for a, b in zip(gaps[0]+gaps[1], gs)]


def pivots(matrix):
    """Exact rational Gauss-Jordan elimination."""
    a = [list(map(F, row)) for row in matrix]
    result, row = [], 0
    for col in range(len(a[0])):
        selected = next((j for j in range(row, len(a)) if a[j][col]), None)
        if selected is None:
            continue
        a[row], a[selected] = a[selected], a[row]
        factor = a[row][col]
        a[row] = [v/factor for v in a[row]]
        for j in range(len(a)):
            if j != row and a[j][col]:
                factor = a[j][col]
                a[j] = [v-factor*w for v, w in zip(a[j], a[row])]
        result.append(col)
        row += 1
    return result


def replay(gaps, ranks):
    colors = {f: r for r, orb in zip(ranks, ORBIT_IDS) for f in orb}
    hands = []
    for start, count, gs in ((0, 9, gaps[:10]), (9, 7, gaps[10:])):
        hand = []
        for i in range(count):
            hand.extend([(0, None)]*gs[i])
            hand.append((colors[start+i], start+i))
        hand.extend([(0, None)]*gs[-1])
        hands.append(deque(hand))
    key = lambda leader: (tuple(r for r, _ in hands[0]),
                          tuple(r for r, _ in hands[1]), leader)
    start = key(0)
    assert Counter(start[0]+start[1]) == {0: 36, 1: 4, 2: 4, 3: 4, 4: 4}
    leader, boundaries, lengths = 0, [], []
    for i in range(6):
        boundaries.append(key(leader))
        player, claimant, debt = leader, None, 0
        pile, events = [], []
        while True:
            assert hands[player]
            card = hands[player].popleft()
            rank, physical_id = card
            pile.append(card)
            if rank:
                events.append((player, physical_id))
                claimant, debt, player = player, rank, player ^ 1
            elif debt:
                debt -= 1
                if debt == 0:
                    hands[claimant].extend(pile)
                    leader = claimant
                    break
            else:
                player ^= 1
        assert tuple(events) == EVENTS[i] and leader == WINNERS[i]
        lengths.append(len(pile))
    assert key(leader) == start and len(set(boundaries)) == 6
    assert lengths == [4, 6, 4, 15, 5, 4]
    return {"A": "".join(SYMBOLS[r] for r in start[0]),
            "B": "".join(SYMBOLS[r] for r in start[1]),
            "leader": "A", "primitive_tricks": 6,
            "individual_plays": sum(lengths), "pile_lengths": lengths}


def check():
    variables = [Affine.variable(i) for i in range(NVAR)]
    gs, ranks = variables[:18], variables[18:]
    x, y, z, w = ranks
    u = gs[16]
    equations = derive_return_equations(gs, ranks)
    assert equations == stated_equations(gs, ranks)
    assert pivots([eq.c[:18] for eq in equations]) == [i for i in range(18) if i != 16]
    formulas = gap_formulas(u, x, y, z, w)
    assert formulas[16] == u
    assert all(eq.substitute(formulas+ranks) == 0 for eq in equations)
    # Rank17 plus explicit affine solutions proves completeness of this family.
    assert 12*sum(formulas) == 115*u+34*x+2*y-100*z+125*w-63
    eliminate_w = variables[:]
    eliminate_w[21] = 10-x-y-z
    assert (12*sum(formulas)-432).substitute(eliminate_w) == \
           115*u-(91*x+123*y+225*z-755)

    # Each physical face orbit has size4, so x,y,z,w are distinct1,...,4.
    # With 36 ordinary cards, integer u gives -24x+8y-5z ==65 (mod115).
    lo, hi = -24*4+8*1-5*4, -24*1+8*4-5*1
    assert (lo, hi) == (-108, 3)
    assert [n for n in range(lo, hi+1) if n % 115 == 65] == [-50]
    # Thus24x-8y+5z=50. Mod8 forces z=2.
    assert [v for v in range(1, 5) if 5*v % 8 == 50 % 8] == [2]
    z_value = 2
    xy = [(a, b) for a in range(1, 5) for b in range(1, 5)
          if 3*a-b == 5 and len({a, b, z_value}) == 3]
    assert xy == [(3, 4)]
    x_value, y_value = xy[0]
    w_value = 10-x_value-y_value-z_value
    u_value = F(91*x_value+123*y_value+225*z_value-755, 115)
    assert w_value == 1 and u_value == 4
    actual_ranks = (x_value, y_value, z_value, w_value)
    actual_gaps = gap_formulas(u_value, *map(F, actual_ranks))
    assert all(v >= 0 and v.denominator == 1 for v in actual_gaps)
    actual_gaps = list(map(int, actual_gaps))
    assert sum(actual_gaps) == 36
    return {"scope": "Unique rank/gap realization of the specified six-trick skeleton with standard inventory",
            "global_skeleton_exclusion_checked_here": False,
            "independent_fifo_transport_matches_all_18_stated_equations": True,
            "face_permutation_orbits_verified": True,
            "return_equation_rank": 17, "free_gap": "b6",
            "affine_parameterization_complete": True,
            "total_count_identity": "12*C=115*u+34*x+2*y-100*z+125*w-63",
            "congruence": "-24*x+8*y-5*z = 65 (mod 115)",
            "congruence_interval": [lo, hi], "unique_residue_representative": -50,
            "unique_ranks_xyzw": list(actual_ranks), "unique_u": int(u_value),
            "unique_gaps": actual_gaps, "direct_replay": replay(actual_gaps, actual_ranks)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = check()
    if args.json:
        args.json.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
