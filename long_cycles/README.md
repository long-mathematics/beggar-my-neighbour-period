# Long periodic Beggar-My-Neighbour games

Companion to the repository's shortest-cycle paper `minimum_period.tex`.
This directory gives **explicit lower bounds**, not global maxima.
The rules are chronological pickup, winner leads, and completed-trick
boundary rank states with the next leader included. `C` represents any
ordinary card.

| Entry condition | Primitive tricks | Plays per cycle | Preperiod | Reverse basin | Balanced ancestors |
| --- | ---: | ---: | ---: | ---: | ---: |
| 26–26 starting deal | **156** | **1,284** | 2 tricks / 22 plays | 7,992 | 72 |
| Any nonempty split (38–14) | **200** | 1,264 | 0 | 6,352 | 0 |
| Any nonempty split (50–2) | 176 | 1,228 | 0 | 6,760 | 0 |

**Paper:** [LaTeX source](long_cycles.tex); the PDF is built and attached
as a GitHub Actions artifact on the relevant commit. A compiled PDF is also
available from the accompanying research conversation.

Run `python3 long_cycles/verify.py` from the repository root, or
`make verify-long-cycles`. This uses only the Python standard library and:

1. checks all inventories and the exact full rank-state primitive periods
   with two independent forward simulators;
2. proves that the balanced 156-trick witness enters after two tricks;
3. checks all twelve protected module passes and the two fixed ordinary
   modules against a `JC` reservoir; and
4. exhausts **all** single-trick predecessors of each orbit, checking every
   returned inverse edge by forward replay.

The compact committed report is
[verification/long_cycle_checks.json](verification/long_cycle_checks.json).
To regenerate it exactly:

```
python3 long_cycles/verify.py --json long_cycles/verification/long_cycle_checks.json
```

The full 200- and 176-trick cycles have no 26–26 ancestors in their complete
backward components. This does not exclude longer cycles accessible from
balanced deals elsewhere in the state graph.

The constructive 156-trick proof uses a 24-card module
`P=CCKCCCQCCCCQCKKCKQCAAQAA` against a `JC` reservoir plus ordinary
spacers `C^2` and `C^20`. Twelve distinct module phases each cost seven
tricks and 59 plays. The spacer costs are 2/6 and 4/42 tricks/plays, giving
12 rounds of 13 tricks and 107 plays.

References and precise qualifications appear in the paper. The published
62-trick/440-play balanced construction of Casella et al. (2025) is the
historical comparison; see DOI 10.1080/00029890.2025.2558484.
