#!/usr/bin/env python3
"""Self-contained long-cycle certificates for standard 52-card Beggar-My-Neighbour.

No dependencies beyond Python's standard library. States are (A, B, leader),
queues front first; captured piles append in chronological order. This script
checks exact primitive periods, a protected queue-module decomposition, and
complete inverse components. Results are printed as JSON.
"""
import argparse
from collections import Counter, deque
import json
from pathlib import Path

PAY = {'J': 1, 'Q': 2, 'K': 3, 'A': 4}
INV = Counter(C=36, J=4, Q=4, K=4, A=4)
BALANCED = ('CCCCCCCCCCJCCCCCCCCQCKCKQK', 'CCCCCCCCJCCKQCAAQAAJCCJCCC', 0)
UNRESTRICTED_200 = ('CCCCAQCACKJCCACCCCCJCCCCCACCJCCKCCCQCC', 'CCQCKCCCQCKCJC', 0)
UNRESTRICTED_176 = ('CCKCCCQCCCCCCCCCCKCKQCQCKQCACAJCCACACCCJCCCCCCCCJC', 'JC', 0)
P = 'CCKCCCQCCCCQCKKCKQCAAQAA'


def step(s):
    """One trick, independently tracking each queue's read offset."""
    hands = [s[0], s[1]]
    if not all(hands):
        return None, 0
    used = [0, 0]
    player, debt, claimant, pile = s[2], 0, None, []
    while used[player] < len(hands[player]):
        card = hands[player][used[player]]
        used[player] += 1
        pile.append(card)
        if card in PAY:
            claimant, debt, player = player, PAY[card], 1 - player
        elif debt:
            debt -= 1
            if debt == 0:
                out = [hands[i][used[i]:] for i in (0, 1)]
                out[claimant] += ''.join(pile)
                return (out[0], out[1], claimant), len(pile)
        else:
            player = 1 - player
    return None, len(pile)


def step_blocks(s):
    """Independent implementation: opening alternation, then payments."""
    hands = [deque(s[0]), deque(s[1])]
    if not all(hands):
        return None, 0
    player, pile = s[2], []
    while True:
        if not hands[player]:
            return None, len(pile)
        card = hands[player].popleft()
        pile.append(card)
        if card != 'C':
            claimant = player
            break
        player ^= 1
    while True:
        opponent = 1 - claimant
        for _ in range(PAY[card]):
            if not hands[opponent]:
                return None, len(pile)
            card = hands[opponent].popleft()
            pile.append(card)
            if card != 'C':
                claimant = opponent
                break
        else:
            hands[claimant].extend(pile)
            return (''.join(hands[0]), ''.join(hands[1]), claimant), len(pile)


def trace(initial):
    """Return (transient tricks, transient plays, cycle tricks, cycle plays, orbit)."""
    seen, states, moves = {}, [], 0
    s = initial
    while s not in seen:
        assert Counter(s[0] + s[1]) == INV
        seen[s] = (len(states), moves)
        states.append(s)
        nxt, p = step(s)
        assert (nxt, p) == step_blocks(s)
        if nxt is None:
            raise AssertionError('A purported cycle terminated')
        s, moves = nxt, moves + p
    start, before = seen[s]
    return start, before, len(states)-start, moves-before, states[start:]


def packet_owners(packet, leader):
    owner, debt, claimant = leader, 0, None
    contributed = [[], []]
    for i, card in enumerate(packet):
        contributed[owner].append(card)
        if card in PAY:
            claimant, debt, owner = owner, PAY[card], 1-owner
        elif debt:
            debt -= 1
            if debt == 0:
                if i != len(packet)-1:
                    return None
                return ''.join(contributed[0]), ''.join(contributed[1]), claimant
        else:
            owner ^= 1
    return None


def predecessors(s):
    """Every possible live predecessor under exactly one completed trick."""
    w = s[2]
    hand = s[w]
    out = set()
    for size in range(2, len(hand)+1):
        packet = hand[-size:]
        for leader in (0, 1):
            owners = packet_owners(packet, leader)
            if owners is None or owners[2] != w:
                continue
            prev = [s[0], s[1]]
            prev[w] = hand[:-size]
            prev = (owners[0] + prev[0], owners[1] + prev[1], leader)
            if not prev[0] or not prev[1]:
                continue
            if step(prev) == (s, size):
                out.add(prev)
    return out


def basin(orbit):
    """Unrestricted complete reverse BFS, cross-check every accepted edge."""
    q = deque(orbit)
    depth = {s: 0 for s in orbit}
    edges = 0
    while q:
        target = q.popleft()
        for prev in predecessors(target):
            assert step(prev)[0] == target
            edges += 1
            if prev not in depth:
                depth[prev] = depth[target] + 1
                q.append(prev)
    balanced = [s for s in depth if len(s[0]) == 26]
    return dict(states=len(depth), edges=edges, balanced=len(balanced),
                maximal_transient=max(depth.values()),
                maximal_smaller_hand=max(min(len(s[0]),len(s[1])) for s in depth),
                balanced_entry_depths=sorted(set(depth[s] for s in balanced)))


def module_pass(piece):
    """Guard a JC-module with an unread sentinel; it must restore JC."""
    hands = [deque(piece+'J*'), deque('JC')]
    leader = tricks = moves = 0
    winners = []
    while True:
        player, debt, claimant, pile = leader, 0, None, []
        while True:
            assert hands[player] and hands[player][0] != '*', 'Marker was read'
            c = hands[player].popleft()
            pile.append(c)
            if c != 'C':
                claimant, debt, player = player, PAY[c], 1-player
            elif debt:
                debt -= 1
                if debt == 0:
                    hands[claimant].extend(pile)
                    leader = claimant
                    break
            else:
                player ^= 1
        tricks += 1
        moves += len(pile)
        winners.append('AB'[leader])
        assert tricks <= 100
        if hands[0] and hands[0][0] == '*':
            assert leader == 0 and ''.join(hands[1]) == 'JC'
            rem = ''.join(hands[0])
            assert rem.endswith('JC')
            new_piece = 'C'+rem[1:-2]
            assert Counter(new_piece) == Counter(piece) and 'J' not in new_piece
            return new_piece, tricks, moves, ''.join(winners)


def verify():
    expected = [
        ('balanced156', BALANCED, (2, 22, 156, 1284), (7992, 7992, 72, 5)),
        ('unrestricted200', UNRESTRICTED_200, (0, 0, 200, 1264), (6352, 6352, 0, None)),
        ('unrestricted176', UNRESTRICTED_176, (0, 0, 176, 1228), (6760, 6760, 0, 6)),
    ]
    report = {'inventory':dict(INV),'conventions':'chronological pickup; winner leads; named rank queues'}
    for name, start, totals, basin_sizes in expected:
        assert Counter(start[0]+start[1]) == INV
        vals = trace(start)
        assert vals[:4] == totals, (name,vals[:4],totals)
        assert len(vals[4]) == len(set(vals[4])) == totals[2]
        detail = {'start':{'A':start[0], 'B':start[1], 'leader':'AB'[start[2]]},
                  'transient_tricks':vals[0], 'transient_plays':vals[1],
                  'primitive_tricks':vals[2], 'cycle_plays':vals[3]}
        bc = basin(vals[4])
        assert (bc['states'],bc['edges'],bc['balanced']) == basin_sizes[:3]
        if basin_sizes[3] is not None:
            assert bc['maximal_transient'] == basin_sizes[3]
        if name == 'balanced156':
            assert len(start[0]) == len(start[1]) == 26
            assert bc['balanced_entry_depths'] == [2]
        if name == 'unrestricted200':
            assert bc['maximal_smaller_hand'] == 24
        detail['complete_predecessor_component'] = bc
        report[name] = detail
    # Certified exact protected piece returns and the primitive 12-phase clock.
    phase, seen, module_plays = P, set(), []
    for j in range(12):
        assert phase not in seen
        seen.add(phase)
        next_phase, t, m, word = module_pass(phase)
        assert (t,m,word) == (7,59,'BBBBAAA')
        module_plays.append(m)
        phase = next_phase
    assert phase == P
    assert module_pass('CC') == ('CC',2,6,'BA')
    assert module_pass('C'*20) == ('C'*20,4,42,'BBBA')
    assert 12*(7+2+4) == 156 and sum(module_plays)+12*(6+42) == 1284
    report['protected_module'] = {'piece':P,'phases':12,'tricks_per_pass':7,
      'plays_per_pass':59,'spacers':{'C2':{'tricks':2,'plays':6},
                                  'C20':{'tricks':4,'plays':42}},
      'round_tricks':13,'round_winner_word':'AAAABBBABAAAB'}
    # Check both entry tricks are exactly 19 and 3 plays.
    s = BALANCED
    entry = []
    for _ in range(2):
        s,n = step(s)
        entry.append(n)
    assert entry == [19,3]
    report['balanced156']['entry_pile_lengths'] = entry
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path, help='Write the result as formatted JSON')
    args = parser.parse_args()
    result = verify()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2,sort_keys=True)+'\n')
    print(json.dumps(result, indent=2,sort_keys=True))
