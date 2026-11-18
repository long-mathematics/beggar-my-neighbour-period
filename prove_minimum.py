#!/usr/bin/env python3
"""Reproduce the minimum completed-trick rank period for Beggar-My-Neighbour.

Dependency: Python 3 and z3-solver (``python -m pip install z3-solver``).
Run: ``python prove_minimum.py --json minimum_verification.json``.
Add ``--structural`` to prove additional facts allowing any number of ordinary
cards: periods 2, 3 and 5 are impossible, and period 4 is possible precisely
when their number is 104+31*n for some nonnegative integer n.

Conventions
-----------
There are two FIFO queues containing 36 ordinary cards and four each of J, Q,
K, A. These special ranks demand 1, 2, 3, 4 cards. An interrupting special
starts a fresh demand. Collected cards are appended in chronological playing
order, and the winner leads. States are taken immediately after collection,
with empty table and no outstanding demand. The player to lead is part of
the state. Ordinary cards are indistinguishable, as are equal special ranks.
The initial split is unrestricted. Distinct physical-card periods differ.

What is proved
--------------
No rank-state cycle has 1, 2, 3, 4, or 5 completed tricks. A supplied 52-card
example has least period 6. The 2--5 lower bound is an exhaustive finite
enumeration followed by exact linear integer arithmetic, not random search.
An SMT result other than UNSAT is fatal to the lower-bound claim.

Why the enumeration is complete
------------------------------
* Both players must win in a cycle: if one never wins, their finite hand
  strictly loses cards. In particular a one-trick cycle is impossible.
* Both players must retain a special at every boundary. Once a hand has no
  special, it cannot win again and is eventually exhausted.
* Within a trick, owners of successive specials alternate. If a trick ends
  with winner w and contains m=2k+e specials, e in {0,1}, its loser supplies k
  specials and its winner supplies k+e. The winner therefore gains exactly k
  specials. Since the loser must retain a special, 0<=k<=7 and 1<=m<=15.
* A periodic sequence of tricks has signed sum of the k's equal to zero.
  All nonconstant binary winner words are considered, up to cyclic rotation
  and exchanging players, with final winner A and initial leader A.
* For every winner word, all feasible k's, e's and initial special-card
  splits 1..15 are tried. Their face-only FIFO play is completely determined.
* The resulting permutation of the sixteen initial special slots must
  preserve rank. Hence every permutation orbit has a single rank, and those
  orbits must be colorable with exactly four cards of each rank.
* For each surviving skeleton, the eighteen initial ordinary-card gaps are
  arbitrary nonnegative integers summing to 36. The SMT constraints below
  express each trick and return of all gaps exactly. No card ordering is
  otherwise assumed and no initial hand size is fixed.

The special skeletons survive in counts 2, 10, 163, 1026 for p=2,3,4,5.
The represented rank assignments number 48, 288, 20328, 134592 respectively.
These counts are checked, but are not used to prune the enumeration.
"""

from __future__ import annotations
import argparse
from collections import Counter, deque
from itertools import product
import json
from pathlib import Path
import time

try:
    import z3
except ImportError as exc:
    raise SystemExit("Install the dependency first: python -m pip install z3-solver") from exc

N_SPECIAL = 16
RANK_SYMBOL = "CJQKA"
EXPECTED = {2: (2, 48), 3: (10, 288), 4: (163, 20328), 5: (1026, 134592)}


def permutation_cycles(permutation):
    assert sorted(permutation) == list(range(len(permutation)))
    seen, result = set(), []
    for i in range(len(permutation)):
        if i in seen:
            continue
        cycle = []
        while i not in seen:
            seen.add(i)
            cycle.append(i)
            i = permutation[i]
        result.append(cycle)
    return result


def winner_patterns(period):
    """All binary necklaces modulo complement, represented with final A=0."""
    representatives = set()
    for word in product((0, 1), repeat=period):
        if len(set(word)) < 2:
            continue
        images = []
        for exchange in (0, 1):
            renamed = tuple(x ^ exchange for x in word)
            for cut in range(period):
                rotated = renamed[cut:] + renamed[:cut]
                if rotated[-1] == 0:
                    images.append(rotated)
        representatives.add(max(images))
    return sorted(representatives, reverse=True)


def count_rank_colorings(lengths):
    """Count all four-color orbit assignments, with weight four per color."""
    states = {(0, 0, 0, 0): 1}
    for length in lengths:
        next_states = {}
        for counts, multiplicity in states.items():
            for rank in range(4):
                if counts[rank] + length <= 4:
                    new = list(counts)
                    new[rank] += length
                    new = tuple(new)
                    next_states[new] = next_states.get(new, 0) + multiplicity
        states = next_states
    return states.get((4, 4, 4, 4), 0)


def skeletons(period):
    """Yield every viable face-only skeleton, without ordinary-gap assumptions."""
    coloring_cache = {}
    for winners in winner_patterns(period):
        assert winners[-1] == 0
        for prefix in product(range(8), repeat=period - 1):
            last = -sum(k * (1 if w == 0 else -1) for k, w in zip(prefix, winners))
            if not 0 <= last <= 7:
                continue
            transfers = prefix + (last,)
            for parity in product((0, 1), repeat=period):
                face_counts = tuple(2 * k + e for k, e in zip(transfers, parity))
                if not all(1 <= m <= 15 for m in face_counts):
                    continue
                for initial_a in range(1, 16):
                    current_a, possible = initial_a, True
                    for transfer, winner in zip(transfers, winners):
                        current_a += transfer if winner == 0 else -transfer
                        if not 1 <= current_a <= 15:
                            possible = False
                            break
                    if not possible:
                        continue
                    hands = [deque(range(initial_a)), deque(range(initial_a, 16))]
                    itinerary = []
                    for winner, face_count in zip(winners, face_counts):
                        pile, events = [], []
                        for j in range(face_count):
                            player = winner ^ ((face_count - 1 - j) % 2)
                            if not hands[player]:
                                possible = False
                                break
                            face = hands[player].popleft()
                            pile.append(face)
                            events.append((player, face))
                        if not possible:
                            break
                        hands[winner].extend(pile)
                        itinerary.append(events)
                    if not possible:
                        continue
                    assert len(hands[0]) == initial_a
                    permutation = list(hands[0]) + list(hands[1])
                    orbits = permutation_cycles(permutation)
                    lengths = tuple(sorted(map(len, orbits), reverse=True))
                    if max(lengths) > 4:
                        continue
                    if lengths not in coloring_cache:
                        coloring_cache[lengths] = count_rank_colorings(lengths)
                    if not coloring_cache[lengths]:
                        continue
                    yield {
                        "A_face_count": initial_a,
                        "winners": winners,
                        "pile_face_counts": face_counts,
                        "face_events": itinerary,
                        "output_slot_to_input_id": permutation,
                        "permutation_cycles": orbits,
                        "rank_coloring_count": coloring_cache[lengths],
                    }


def gap_problem(case, ordinary_count=36):
    """Exact integer constraints for fillings of a skeleton; None frees C count."""
    a = case["A_face_count"]
    orbits = case["permutation_cycles"]
    orbit_ranks = [z3.Int(f"rank_{i}") for i in range(len(orbits))]
    ranks = [None] * 16
    for variable, orbit in zip(orbit_ranks, orbits):
        for face in orbit:
            ranks[face] = variable
    gaps = [z3.Int(f"gap_{i}") for i in range(18)]
    original_faces = [list(range(a)), list(range(a, 16))]
    original_gaps = [gaps[:a + 1], gaps[a + 1:]]
    faces = [h[:] for h in original_faces]
    hand_gaps = [h[:] for h in original_gaps]
    solver = z3.Solver()
    solver.add(*[gap >= 0 for gap in gaps])
    if ordinary_count is not None:
        solver.add(z3.Sum(gaps) == ordinary_count)
    solver.add(*[z3.And(rank >= 1, rank <= 4) for rank in orbit_ranks])
    for rank in range(1, 5):
        solver.add(z3.Sum([z3.If(v == rank, len(orbit), 0)
                           for v, orbit in zip(orbit_ranks, orbits)]) == 4)
    leader = 0
    for events in case["face_events"]:
        first, face = events[0]
        assert faces[first][0] == face
        first_gap = hand_gaps[first][0]
        other = 1 - first
        offset = int(first != leader)
        # Before the first special, cards alternate. If the nonleader has the
        # first special, the leader has supplied one extra ordinary card.
        solver.add(hand_gaps[other][0] >= first_gap + offset)
        hand_gaps[other][0] -= first_gap + offset
        faces[first].pop(0)
        hand_gaps[first].pop(0)
        pile_faces = [face]
        pile_gaps = [2 * first_gap + offset]
        previous_player, previous_face = first, face
        for player, face in events[1:]:
            assert player == 1 - previous_player
            assert faces[player] and faces[player][0] == face
            gap = hand_gaps[player][0]
            solver.add(gap >= 0, gap < ranks[previous_face])
            faces[player].pop(0)
            hand_gaps[player].pop(0)
            pile_faces.append(face)
            pile_gaps.append(gap)
            previous_player, previous_face = player, face
        winner, loser = previous_player, 1 - previous_player
        payment = ranks[previous_face]
        assert faces[loser]  # Necessary for membership in an infinite cycle.
        solver.add(hand_gaps[loser][0] >= payment)
        hand_gaps[loser][0] -= payment
        # Append the chronological pile, merging its first gap with the tail.
        hand_gaps[winner][-1] += pile_gaps[0]
        hand_gaps[winner].extend(pile_gaps[1:] + [payment])
        faces[winner].extend(pile_faces)
        leader = winner
    assert leader == 0
    for player in (0, 1):
        assert len(faces[player]) == len(original_faces[player])
        for old_face, new_face in zip(original_faces[player], faces[player]):
            assert ranks[old_face].eq(ranks[new_face])
        assert len(hand_gaps[player]) == len(original_gaps[player])
        solver.add(*[new == old for old, new in
                     zip(original_gaps[player], hand_gaps[player])])
    return solver


def decode(word):
    return tuple(RANK_SYMBOL.index(char) for char in word)


def encode(cards):
    return "".join(RANK_SYMBOL[card] for card in cards)


def trick(state):
    """Card-by-card reference implementation, independent of the gap model."""
    hands = [deque(state[0]), deque(state[1])]
    player, claimant, debt = state[2], None, 0
    pile, events = [], []
    while hands[player]:
        card = hands[player].popleft()
        pile.append(card)
        events.append((player, card))
        if card:
            claimant, debt = player, card
            player = 1 - player
        elif debt:
            debt -= 1
            if debt == 0:
                hands[claimant].extend(pile)
                return (tuple(hands[0]), tuple(hands[1]), claimant), events
        else:
            player = 1 - player
    return None, events


def challenge_trick(state):
    """Second implementation: process a whole challenge at a time."""
    hands = [list(state[0]), list(state[1])]
    player, claimant, debt = state[2], None, 0
    pile, events = [], []
    while True:
        allowance, answering = debt or 1, debt != 0
        interrupted = False
        for _ in range(allowance):
            if not hands[player]:
                return None, events
            card = hands[player].pop(0)
            pile.append(card)
            events.append((player, card))
            if card:
                claimant, debt = player, card
                player = 1 - player
                interrupted = True
                break
        if interrupted:
            continue
        if answering:
            hands[claimant].extend(pile)
            return (tuple(hands[0]), tuple(hands[1]), claimant), events
        player = 1 - player


def verify_witness():
    initial = (decode("KCACCCCCQCCCQCACCCQKCACCCCCQCC"),
               decode("CJCKCJCCAKCCCCCJCCCCJC"), 0)
    assert Counter(initial[0] + initial[1]) == {0: 36, 1: 4, 2: 4, 3: 4, 4: 4}
    state, seen, rows = initial, set(), []
    for number in range(1, 7):
        assert state not in seen, "The claimed primitive period is too long."
        seen.add(state)
        after, events = trick(state)
        assert (after, events) == challenge_trick(state)
        assert after is not None, "Witness terminates."
        rows.append({
            "trick": number,
            "A_before": encode(state[0]),
            "B_before": encode(state[1]),
            "leader": "AB"[state[2]],
            "plays": [["AB"[player], RANK_SYMBOL[card]] for player, card in events],
            "pile": encode([card for player, card in events]),
            "winner": "AB"[after[2]],
            "A_after": encode(after[0]),
            "B_after": encode(after[1]),
        })
        state = after
    assert state == initial, "Witness does not return after six tricks."
    return {
        "A": encode(initial[0]), "B": encode(initial[1]), "leader": "A",
        "split": [len(initial[0]), len(initial[1])], "least_trick_period": 6,
        "card_plays_per_period": sum(len(row["plays"]) for row in rows),
        "trace": rows,
    }


def verify_balanced_entry(witness):
    """A 26--26 deal enters the displayed cycle after one elementary trick."""
    state = (decode("ACCCQKCACCCCCQCCCQCACCCQKC"),
             decode("CCCCCJCCCCJCKCJCCAKCCCCCJC"), 0)
    assert len(state[0]) == len(state[1]) == 26
    assert Counter(state[0] + state[1]) == {0: 36, 1: 4, 2: 4, 3: 4, 4: 4}
    after, events = trick(state)
    assert (after, events) == challenge_trick(state)
    assert events == [(0, 4), (1, 0), (1, 0), (1, 0), (1, 0)]
    fourth = witness["trace"][3]
    assert after == (decode(fourth["A_after"]), decode(fourth["B_after"]), 0)
    assert all(state != (decode(row["A_before"]), decode(row["B_before"]),
                         "AB".index(row["leader"])) for row in witness["trace"])
    return {"A": encode(state[0]), "B": encode(state[1]), "leader": "A",
            "split": [26, 26], "transient_tricks": 1, "eventual_least_trick_period": 6,
            "entry_pile": "ACCCC", "enters_after_displayed_trick": 4}


def structural_checks():
    """Optional stronger statements, keeping four specials of each rank."""
    result, feasible_four = {}, []
    for period in range(2, 6):
        cases, satisfiable = 0, 0
        for case in skeletons(period):
            cases += 1
            solver = gap_problem(case, ordinary_count=None)
            status = solver.check()
            if status == z3.unknown:
                raise RuntimeError("Structural check returned unknown: " + solver.reason_unknown())
            if status == z3.sat:
                satisfiable += 1
                if period != 4:
                    raise RuntimeError(f"Unexpected unrestricted-C solution for p={period}: {solver.model()}")
                feasible_four.append(case)
        assert cases == EXPECTED[period][0]
        result[str(period)] = {"skeletons": cases, "feasible_skeletons_with_any_C_count": satisfiable}
        print(f"Structural p={period}: {cases:,} skeletons; {satisfiable} feasible with unrestricted C count.", flush=True)
    assert len(feasible_four) == 1
    case = feasible_four[0]
    assert case["A_face_count"] == 8
    assert tuple(case["winners"]) == (1, 0, 1, 0)
    assert tuple(case["pile_face_counts"]) == (1, 1, 1, 1)
    solver = gap_problem(case, ordinary_count=None)
    total = z3.Sum([z3.Int(f"gap_{i}") for i in range(18)])
    solver.push()
    solver.add(z3.Or(total < 104, total % 31 != 104 % 31))
    status = solver.check()
    if status != z3.unsat:
        raise RuntimeError("Four-trick necessary C count not proved: " + str(status))
    solver.pop()
    # A symbolic family supplies the converse for every n>=0. Each hand has
    # eight alternating specials: A,J,A,J,A,J,A,J and Q,K,Q,K,Q,K,Q,K.
    # Entries below are the gaps before each special and the final tail.
    n = z3.Int("family_n")
    E, O = 4 + 2 * n, 9 + 2 * n
    family_gaps = [E, O] * 4 + [z3.IntVal(1)] + [n, O, E, O, E, O, E, O, z3.IntVal(3)]
    assert len(family_gaps) == 18
    substitutions = [(z3.Int(f"gap_{i}"), gap) for i, gap in enumerate(family_gaps)]
    substitutions += [(z3.Int(f"rank_{i}"), z3.IntVal(rank))
                      for i, rank in enumerate((4, 1, 2, 3))]
    identity_checker = z3.Solver()
    all_conditions = z3.And(*[z3.substitute(assertion, *substitutions)
                              for assertion in solver.assertions()])
    identity_checker.add(n >= 0, z3.Not(all_conditions))
    status = identity_checker.check()
    if status != z3.unsat:
        raise RuntimeError("Four-trick family not proved for all n>=0: " + str(status))
    assert z3.is_true(z3.simplify(z3.Sum(family_gaps) == 104 + 31 * n))
    result["four_trick_ordinary_counts"] = {"formula": "104 + 31*n", "n": "every integer >= 0",
                                           "necessity_and_sufficiency_verified": True}
    print("Structural p=4: C counts are exactly 104+31*n, n>=0; necessity and symbolic converse VERIFIED.", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, help="Write machine-readable counts and the complete witness trace.")
    parser.add_argument("--smt-dir", type=Path, help="Optionally export every exact SMT-LIB problem for independent checking.")
    parser.add_argument("--structural", action="store_true", help="Also check unrestricted-C impossibility for p=2,3,5 and the complete p=4 C-count theorem.")
    args = parser.parse_args()
    if args.smt_dir:
        args.smt_dir.mkdir(parents=True, exist_ok=True)
    print("One trick is impossible: its loser strictly loses cards.", flush=True)
    result = {"z3_version": z3.get_version_string(), "ordinary_cards": 36,
              "special_rank_multiplicities": [4, 4, 4, 4], "lower_bound_checks": []}
    for period in range(2, 6):
        started, cases, colorings = time.monotonic(), 0, 0
        for case in skeletons(period):
            cases += 1
            colorings += case["rank_coloring_count"]
            solver = gap_problem(case)
            if args.smt_dir:
                (args.smt_dir / f"period_{period}_case_{cases:04d}.smt2").write_text(solver.to_smt2())
            status = solver.check()
            if status != z3.unsat:
                failure = {"period": period, "case_number": cases, "status": str(status), "case": case}
                if status == z3.sat:
                    failure["model"] = str(solver.model())
                else:
                    failure["reason_unknown"] = solver.reason_unknown()
                raise RuntimeError("Lower bound NOT established: " + json.dumps(failure))
        assert (cases, colorings) == EXPECTED[period], (period, cases, colorings)
        elapsed = time.monotonic() - started
        print(f"p={period}: {cases:,} skeletons, {colorings:,} rank assignments; ALL UNSAT ({elapsed:.2f}s).", flush=True)
        result["lower_bound_checks"].append({"period": period, "skeletons": cases,
                                             "represented_rank_assignments": colorings,
                                             "all_unsat": True, "seconds": elapsed})
    witness = verify_witness()
    result["witness"] = witness
    result["balanced_entry"] = verify_balanced_entry(witness)
    result["minimum_completed_trick_rank_period"] = 6
    print("\nSix-trick witness: A leads; queue fronts are at the left.")
    print("A:", witness["A"])
    print("B:", witness["B"])
    for row in witness["trace"]:
        plays = " ".join(f"{player}:{card}" for player, card in row["plays"])
        print(f"Trick {row['trick']}: {plays}; pile {row['pile']}; winner {row['winner']}.")
        print(f"  A={row['A_after']}; B={row['B_after']}")
    print("\nVERIFIED: minimum p over all nonempty splits is 6; this cycle uses 38 individual card plays.")
    print("A balanced deal enters this cycle after A plays an ace and B pays four ordinary cards:")
    print("  A=" + result["balanced_entry"]["A"])
    print("  B=" + result["balanced_entry"]["B"] + "; A leads.")
    if args.structural:
        result["structural_checks"] = structural_checks()
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
