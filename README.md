# The minimum trick period in Beggar-My-Neighbour

**Result:** Under chronological pickup and winner-led play, the least primitive
*completed-trick* period of a rank-state cycle using the standard 52-card
inventory is **six**. A balanced 26–26 deal enters such a cycle after one
trick. The six-trick return is hand-checkable, while its optimality uses an
exhaustive integer-constraint search.

**Paper:** [minimum_period.pdf](minimum_period.pdf) · [LaTeX source](minimum_period.tex)

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

## Proof and reproducibility

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
Continuous integration independently builds the paper and reruns the checks.

## Scope

The optimality claim is about primitive periods in **completed tricks**, for
a **standard 52-card inventory**, allowing any nonempty split. It also applies
to the minimum *eventual* primitive period reachable from a 26–26 split.

It does **not** establish the smallest number of individual card plays, the
minimum period when all 52 physical cards are distinguished, or a
classification of every six-trick orbit. The lower bound is computer-assisted;
no formally verified proof-assistant certificate is claimed.

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
