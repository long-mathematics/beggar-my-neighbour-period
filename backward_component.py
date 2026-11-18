#!/usr/bin/env python3
"""Exact backward component of the six-trick rank-state cycle (stdlib only).

A state is (A queue, B queue, next leader), with C=0,J=1,Q=2,K=3,A=4.
Captured piles are appended in chronological order. This program exhausts
all legal single-trick predecessors and checks each by forward replay.
"""
from __future__ import annotations
from collections import Counter, deque
import argparse
import json
from pathlib import Path

SYMBOLS = 'CJQKA'
A0 = 'KCACCCCCQCCCQCACCCQKCACCCCCQCC'
B0 = 'CJCKCJCCAKCCCCCJCCCCJC'
BAL_A = 'ACCCQKCACCCCCQCCCQCACCCQKC'
BAL_B = 'CCCCCJCCCCJCKCJCCAKCCCCCJC'


def dec(w): return tuple(SYMBOLS.index(c) for c in w)
def enc(w): return ''.join(SYMBOLS[c] for c in w)


def trick(s):
    h = [deque(s[0]), deque(s[1])]
    player, debt, claimant, pile = s[2], 0, None, []
    while h[player]:
        card = h[player].popleft()
        pile.append(card)
        if card:
            claimant = player
            debt = card
            player ^= 1
        elif debt:
            debt -= 1
            if debt == 0:
                h[claimant].extend(pile)
                return (tuple(h[0]), tuple(h[1]), claimant)
        else:
            player ^= 1
    return None


def packet_owners(packet, lead):
    """Return owners for one legally completed pile, or None.

    Compute turn ownership from the pile word alone. A finished payment must
    occur only at its last card; in a trick there must be a face card.
    """
    cur, debt, claimant = lead, 0, None
    owners = []
    for i, card in enumerate(packet):
        owners.append(cur)
        if card:
            claimant, debt = cur, card
            cur ^= 1
        elif debt:
            debt -= 1
            if debt == 0:
                if i != len(packet) - 1:
                    return None
                return owners, claimant
        else:
            cur ^= 1
    return None


def predecessors(s):
    winner = s[2]
    current = s[winner]
    out = set()
    for length in range(2, len(current) + 1):
        pile = current[-length:]
        leftover = current[:-length]
        for leader in (0, 1):
            result = packet_owners(pile, leader)
            if result is None:
                continue
            owners, reconstructed_winner = result
            if reconstructed_winner != winner:
                continue
            orig = [list(s[0]), list(s[1])]
            orig[winner] = list(leftover)
            for player in (0, 1):
                orig[player] = [card for card, who in zip(pile, owners) if who == player] + orig[player]
            t = (tuple(orig[0]), tuple(orig[1]), leader)
            if not t[0] or not t[1]:
                continue
            if trick(t) == s:
                out.add(t)
    return out


def main():
    p=argparse.ArgumentParser(); p.add_argument('--json',type=Path)
    args=p.parse_args()
    witness=(dec(A0),dec(B0),0)
    cycle=[]; s=witness
    for _ in range(6):
        assert s not in cycle
        cycle.append(s); s=trick(s); assert s is not None
    assert s==witness
    depth={s:0 for s in cycle}
    q=deque(cycle)
    edges=0
    while q:
        cur=q.popleft()
        for prev in predecessors(cur):
            assert trick(prev)==cur
            edges+=1
            if prev not in depth:
                depth[prev]=depth[cur]+1
                q.append(prev)
    balanced=[s for s in depth if len(s[0])==26]
    sample=(dec(BAL_A),dec(BAL_B),0)
    assert len(sample[0])==len(sample[1])==26
    assert sample in depth and depth[sample]==1
    card_inventory=Counter(witness[0]+witness[1])
    assert card_inventory=={0:36,1:4,2:4,3:4,4:4}
    assert all(Counter(s[0]+s[1])==card_inventory for s in depth)
    split_a=sorted(set(len(s[0]) for s in depth if s[2]==0))
    info={
        'cycle_size':len(cycle),
        'backward_component_size':len(depth),
        'balanced_states':len(balanced),
        'maximum_preperiod':max(depth.values()),
        'edge_candidates_verified':edges,
        'A_leads_A_hand_sizes':split_a,
        'balanced_sample':{'A':BAL_A,'B':BAL_B,'next_leader':'A','distance':depth[sample]},
        'balanced_states_list':[{'A':enc(s[0]),'B':enc(s[1]),'next_leader':'AB'[s[2]],'distance':depth[s]} for s in sorted(balanced)],
    }
    print({k:v for k,v in info.items() if k not in ('balanced_states_list','balanced_sample')})
    if args.json:args.json.write_text(json.dumps(info,indent=2)+'\n')

if __name__=='__main__':main()
