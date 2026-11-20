# The unique shortest cycle in Beggar-My-Neighbour

**Result:** Under chronological pickup and winner-led play, the minimum
rank-state period for the standard 52-card inventory is **six completed tricks**
or **38 individual card plays**. The same cycle is the unique minimizer of
both quantities, up to cyclic phase and exchange of the players.

In particular, **every cycle using at most 38 plays is the displayed six-trick
cycle**, allowing every trick count and every nonempty hand split. A balanced
26–26 deal enters it after one trick. The global exclusions are exhaustive
computer-assisted proofs; the surviving pattern's rigidity also has a short
modular-arithmetic proof.

**Paper:** [minimum_period.pdf](minimum_period.pdf) · [LaTeX source](minimum_period.tex)

## Companion paper: long periodic games

A separate manuscript, [**Long Periodic Games of Beggar-My-Neighbour:
Balanced Deals and Protected Queue Modules**](long_cycles/long_cycles.tex),
gives explicit long-cycle witnesses and a reproducible protected-module proof.
[Supporting scripts and certificates](long_cycles/README.md) are independent
of the minimum-period classification.

* An explicit **26–26** deal enters a **156-trick / 1,284-play** primitive cycle
  after two tricks (22 plays).
* An unrestricted **38–14** state has a **200-trick / 1,264-play** cycle.
  A 50–2 state gives a separate **176-trick / 1,228-play** example.
* Complete inverse components have respectively 72, 0, and 0 balanced
  ancestors. The 156-cycle has twelve protected module phases.

These are **lower bounds**, not claims of globally longest possible cycles.
Build with `make paper-long`, verify with `make verify-long-cycles`, or
download the compiled long-cycle paper from the GitHub Actions build artifact.

## Exact witness

`C` means any ordinary card; J, Q, K, A have penalties 1, 2, 3, 4.
Read queues left-to-right. Captured cards are appended in chronological
order. The winner leads the next trick. Initially **A leads**.

```text
A: KCACCCCCQCCCQCACCCQKCACCCCCQCC
B: CJCKCJCCAKCCCCCJCCCCJC
```

A has 30 cards, B 22. The six winners are **BBBABA**, with pile lengths
**4, 6, 4, 15, 5, 4** (38 individual card plays total). After six completed
tricks, both ordered rank queues and the next leader return *exactly*.

An equal-deal ancestor, with A leading, is:

```text
A: ACCCQKCACCCCCQCCCQCACCCQKC
B: CCCCCJCCCCJCKCJCCAKCCCCCJC
```

After one trick, this state enters the six-cycle. Its full backward component
contains **181 rank states**, including **19 balanced 26–26 states**.

A rank state identifies all ordinary cards and identifies copies of the same
face rank. The physical-card labelled period of this witness is 2,376 tricks,
which is a separate concept and is **not** claimed minimal.

## Global 38-play minimum and uniqueness

If a cycle has `p` tricks and `c` changes of winner in its cyclic winner word,
then `L >= 2p + c >= 2p + 2`. A completed trick uses at least two plays; a
two-play trick is the leader's jack followed by an ordinary card, so every
change of winner needs at least three. Both players must win during a cycle.
Consequently **at most 38 plays means at most 18 tricks**. A one-trick return
is impossible.

Two separately implemented C++ enumerators cover every face itinerary for
periods 2–18 and every initial face split. They agree on the complete sets
of **43,808 candidates** retained by the necessary play-budget bounds.
The exact model assigns all face ranks and all 18 ordinary gaps, enforces
the standard inventory and every payment, and requires the queues and
leader to return with at most 38 plays.

| Completed tricks | Candidate face itineraries | Feasible itineraries | Rank/gap models |
|---:|---:|---:|---:|
| 2 | 2 | 0 | 0 |
| 3 | 10 | 0 | 0 |
| 4 | 145 | 0 | 0 |
| 5 | 565 | 0 | 0 |
| 6 | 4,234 | 1 | 1 |
| 7 | 7,119 | 0 | 0 |
| 8 | 13,140 | 0 | 0 |
| 9 | 8,530 | 0 | 0 |
| 10 | 5,178 | 0 | 0 |
| 11 | 3,340 | 0 | 0 |
| 12 | 1,340 | 0 | 0 |
| 13 | 166 | 0 | 0 |
| 14 | 35 | 0 | 0 |
| 15 | 4 | 0 | 0 |
| 16 | 0 | 0 | 0 |
| 17 | 0 | 0 | 0 |
| 18 | 0 | 0 | 0 |
| **Total** | **43,808** | **1** | **1** |

For every satisfiable itinerary, the verifier enumerates all models by
blocking every gap and every face-orbit rank, continuing until `unsat`.
The sole feasible case has **22 essential variables: 18 gaps and four orbit
ranks**. Its only model is the witness above, with exactly 38 plays; the
complete blocking query is unsatisfiable. Thus this classification proves
both the minimum and its uniqueness. Any `unknown` result is an error.

Install the Python dependency and verify the complete archived candidate set:

```bash
python3 -m pip install -r requirements.txt
make verify-plays
```

Regenerate both complete candidate sets with a C++20 compiler, compare every
candidate, and perform the full classification:

```bash
make crosscheck-plays
```

The corresponding standalone command is:

```bash
python3 verify_unique38.py --crosscheck --workers 2 \
    --json verification/play_period/fresh_crosscheck.json
```

The sources are [`bounded_play_skeletons.cpp`](bounded_play_skeletons.cpp),
[`independent_play_skeletons.cpp`](independent_play_skeletons.cpp), and
[`verify_unique38.py`](verify_unique38.py). The verifier uses the same exact
gap model and direct simulators as the earlier trick-period proof, with an
exact individual-play counter. The complete compressed input is
[`play_candidates_le38.tsv.gz`](play_candidates_le38.tsv.gz); reports and
the positive/blocked SMT queries are under
[`verification/play_period/`](verification/play_period/).

The positive and blocked queries can also be checked through the native Z3
C interface, without Python Z3 bindings:

```bash
python3 check_play_queries.py \
    --json verification/play_period/native_query_fresh.json
```

This requires an installed Z3 shared library. To check queries from a fresh
classification, add `--classification verification/play_period/fresh_crosscheck.json`.
The checker verifies their hashes against that report and requires `sat` for
the positive query and `unsat` after blocking all 22 variables. This additional
check covers the surviving case; the full global exclusion is performed by
`verify_unique38.py`.

### Elementary rigidity of the surviving pattern

After deleting ordinary cards, the unique feasible face pattern is
`xyzzyzxyz` in A and `wxwyxww` in B. Its four face-permutation orbits each
have length four, so `(x,y,z,w)` permutes `(1,2,3,4)`. The gap-return system
has rank 17 with sole free gap `u = b6`. Adding its affine solutions gives

```math
12N_C = 115u + 34x + 2y - 100z + 125w - 63.
```

The standard ordinary count `N_C = 36` and rank sum `x+y+z+w = 10` imply
`-24x + 8y - 5z = 65 (mod 115)`. The left side lies in `[-108,3]`, so it
equals `-50`. Hence `24x - 8y + 5z = 50`; reduction modulo eight gives
`z=2`, then distinctness forces `x=3`, `y=4`, `w=1`, and `u=4`.
All eighteen gaps are therefore uniquely determined.

The separate checker derives the return equations by symbolic FIFO transport,
verifies their rank and affine formulas with exact rational arithmetic, and
checks the congruence and direct play. It needs only Python's standard library:

```bash
python3 check_algebraic_rigidity.py \
    --json verification/play_period/algebraic_rigidity.json
```

## Complete classification of six-trick cycles

**The six-trick rank-state cycle is unique up to the rotation of its six
completed tricks and exchange of the two players.** With player names fixed,
there are exactly **two** oriented cycles, each with six boundary states,
exchanged by swapping A and B. The unique equivalence class uses 38 individual
card plays per period. The separate global classification above shows that
this is also the unique shortest cycle when all trick counts are allowed.

The computer-assisted classification first enumerates every possible face-only
itinerary with the same cyclic/relabeling reductions used in the lower-bound
proof. Two implementations, an optimized C++ version and the original Python
version, give **exactly matching sets** of possibilities for each of the seven
canonical winner words:

| Canonical winner word (B=1, A=0) | Candidate face skeletons |
|---|---:|
| 111110 | 199 |
| 111100 | 2,361 |
| 111010 | 2,121 |
| 111000 | 5,286 |
| 110110 | 2,489 |
| 110100 | 4,293 |
| 101010 | 4,658 |
| **Total** | **21,407** |

Together they represent **2,688,096** initial face-rank assignments. Solving
all 18 ordinary-gap constraints for the standard 36-card ordinary inventory
eliminates 21,406 skeletons. The only feasible skeleton has face counts
`2,2,1,5,1,1`, winner word `111010`, nine faces in A, and is the hands shown
above. A second-model blocking clause is unsatisfiable: **its face ranks and
ordinary-card gaps are uniquely determined**. A separate standard-library
rigidity certificate verifies uniqueness within this skeleton using exact
rational arithmetic, without Z3.

To reproduce the complete classification using a C++17/20 compiler and the
native Z3 shared library (`libz3.so.4`), run:

```bash
make classify-six
```

Or run the individual steps:

```bash
c++ -O3 -std=c++20 skeleton6.cpp -o skeleton6
./skeleton6 skeleton6.tsv
python3 classify_six.py --json verification/six_classification_full.json
python3 enumerate_models.py --json verification/six_classification_models.json
```

The C++ program generates `skeleton6.tsv` deterministically. A compressed
copy, [`skeleton6.tsv.gz`](skeleton6.tsv.gz), is committed; to solve without
compiling C++, run `gzip -dc skeleton6.tsv.gz > skeleton6.tsv` first.
The archived output includes six exhaustive, disjoint case-index ranges.
Any solver status other than `sat` or `unsat` aborts the check. This is
an **exhaustive, reproducible computer-assisted proof**, not a formal theorem
proof in Lean or Coq.

To independently compare the two face-only enumerators, run:

```bash
make crosscheck-six
```

The additional script `crosscheck_skeletons.py` checks equality of the
entire candidate set, not just its cardinality, for each winner word.
All seven crosscheck certificates are included under `verification/`.

**Accessibility:** The orientation displayed above has 181 backward-reachable
rank states, including 19 balanced (26–26) states; its player-swapped copy
has another disjoint 181 states, including 19 balanced states. Across both,
there are exactly **38 balanced rank states** reaching a six-trick cycle,
19 with player A leading and 19 with player B leading. These counts are
specific to the rank-state convention and exclude the number of suit-labelled
deals, which is much larger.

A separate **both-orientations backward-basin audit** verifies the symmetry
claim without any SAT/SMT dependency. It reconstructs both backward components
from all six cycle states, checks that exchanging players conjugates their
completed-trick maps, confirms the components are disjoint, and counts all 38
balanced predecessors (19 for each next leader):

```bash
python3 verify_orbit_symmetry.py --json verification/orbit_symmetry_verification.json
```

## Earlier trick-period proof and additional structure

The lower bound enumerates all legal face-card itineraries for periods 2–5 and
solves their complete integer ordinary-gap constraints (18 gaps, 36 ordinary
cards). The exhaustive model produces:

| Period | Face itineraries | Rank colorings represented | Feasible cases |
|---:|---:|---:|---:|
| 2 | 2 | 48 | 0 |
| 3 | 10 | 288 | 0 |
| 4 | 163 | 20,328 | 0 |
| 5 | 1,026 | 134,592 | 0 |

The `prove_minimum.py` implementation requires Python 3 and the `z3-solver`
package. It generates all candidates itself, rejects any solver result other
than `unsat` for the lower bound, simulates the witness with two direct
implementations, and optionally checks the larger structural theorem:

```bash
python3 -m pip install -r requirements.txt
python3 prove_minimum.py --json verification/minimum_fresh.json
python3 prove_minimum.py --structural --json verification/structural_fresh.json
```

An additional path **does not require the Python Z3 bindings**: install a
system `libz3.so.4` (or supply `--lib /path/to/libz3.so`) and run:

```bash
python3 native_z3_check.py --json verification/native_z3_fresh.json
```

This uses the original constraint model with an independent native SMT-LIB
interface via Python `ctypes`. It freshly checked all 1,201 itinerary
exclusions against `libz3.so.4` version 4.13.3. A second interface is not a
separately proved mathematical model; the reduction and its code should still
be audited independently.

The witness-specific checks are independent of Z3:

```bash
python3 backward_component.py --json verification/backward_fresh.json
python3 check_rigidity.py --json verification/rigidity_fresh.json
```

`backward_component.py` verifies all 181 backward-reachable states by forward
replay. `check_rigidity.py` uses exact rational arithmetic to establish
uniqueness of the specific six-trick face itinerary (within its prescribed
pattern), including the 36 ordinary-card total.

The `verification/` directory contains original solver outputs and the fresh
native-Z3, backward-component and rigidity outputs. To regenerate the paper:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error minimum_period.tex
```

The compiled PDF is committed as a first-class file for convenient reading.
Continuous integration builds the paper, reruns the earlier checks, and
regenerates both complete candidate sets for the global play-period proof.

## Scope

The optimality claims concern primitive rank-state periods measured in
**completed tricks** and **individual card plays**, for the **standard
52-card inventory**, allowing any nonempty split. The minima are six tricks
and 38 plays, and their unique attaining orbit is the same. They also apply
to the minimum eventual periods reachable from a 26–26 split.

With player names fixed, there are two oriented cycles, each containing six
completed-trick boundary states. The global exclusion is computer-assisted;
the surviving pattern's rigidity has the elementary arithmetic proof above.
No proof-assistant formalization or independently checked solver proof trace
is claimed. The minimum period with all 52 physical cards distinguished
remains a separate question.

The paper also proves that, fixing a finite special-card inventory and period,
the possible ordinary-card counts form an effectively semilinear set; it
classifies period-four decks with four copies of each face rank as having
exactly `104 + 31n` ordinary cards (`n >= 0`).

## Related work

- M. M. Paulhus, *Beggar My Neighbour*, **American Mathematical Monthly**
  106 (1999), 162–165. [DOI](https://doi.org/10.2307/2589054).
- B. Casella, P. M. Anderson, M. Kleber, R. P. Mann, R. Nessler,
  W. Rucklidge, S. G. Williams, and N. Wu, *A Non-Terminating Game of
  Beggar-My-Neighbor*, **American Mathematical Monthly** 132 (2025),
  978–994. [DOI](https://doi.org/10.1080/00029890.2025.2558484).
- N. Andorno, G. Cernoia, S. Duiz, and A. Michelangeli, *The Dynamical
  Landscape of Beggar-My-Neighbour: Ultra-long Matches, Loops, and Infinite
  Matches*, [arXiv:2602.23406](https://arxiv.org/abs/2602.23406) (2026).
- S. Ginsburg and E. H. Spanier, *Semigroups, Presburger Formulas, and
  Languages*, **Pacific Journal of Mathematics** 16 (1966), 285–296.
  [DOI](https://doi.org/10.2140/pjm.1966.16.285).

The 2025 paper discusses the historical 1991 Great Usenet BYN Contest
organized by Chris Long.

## License

MIT. See [LICENSE](LICENSE).
