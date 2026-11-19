# Individual-play minimum and uniqueness certificates

These certificates establish that the standard 52-card inventory has exactly
one rank-state cycle using at most **38 individual plays**, up to cyclic phase
and exchange of the players. It is the six-trick witness, which uses exactly
38 plays. All nonempty initial splits and all trick periods are covered under
chronological pickup and winner-led play.

A rank state consists of both ordered queues and the next leader at a completed
trick boundary; ordinary cards and copies of the same face rank are identified.
The bound `L >= 2p+c`, with at least two cyclic winner changes, reduces `L <= 38`
to periods 2 through 18. The full classification checks **43,808** candidate
face skeletons, finds one satisfiable skeleton, and exhausts its single rank/gap
model by blocking all **18 gap variables and four orbit-rank variables**.

| File | Scope |
|---|---|
| `classification.json` | Fresh complete classification, both independent generator comparisons, every model of every SAT skeleton, direct replay, canonicalization, and source/input hashes. |
| `known_sat38.smt2` | Exact satisfiable query for the surviving skeleton. |
| `known_sat38_blocked.smt2` | The same query with its complete 22-variable assignment blocked; UNSAT excludes a second model. |
| `native_query_check.json` | Independent native-Z3 checks of those two queries after matching their hashes against the classification report. This checks the surviving case, not the other skeleton exclusions. |
| `algebraic_rigidity.json` | Separate exact-rational, standard-library verification that the surviving skeleton has only the displayed standard-deck realization. This does not enumerate the other skeletons. |

The classification report records the SHA-256 of the compressed and uncompressed
candidate input, all model/enumeration source files used in the run, and both SMT
queries. It also records every candidate count, the unique variable assignment,
the complete witness trace, its balanced ancestor, and the two disjoint oriented
cycles. The native report additionally hashes the exact classification JSON it
checked. These hashes identify the files corresponding to each recorded run.

## Reproduce from the repository root

Regenerate both independently implemented candidate sets, compare every line,
and classify every exact integer model:

```bash
python3 verify_unique38.py --crosscheck --workers 2 \
    --json verification/play_period/fresh_crosscheck.json
```

Omit `--crosscheck` to solve the committed candidate archive without regenerating
it. Python's `z3-solver` package is required; regeneration also needs a C++20
compiler. An unknown solver result, incomplete model enumeration, malformed
candidate, or generator-set disagreement aborts the verification.

Check the matching positive and blocked queries using an installed native Z3
shared library, without requiring the Python Z3 package:

```bash
python3 check_play_queries.py \
    --classification verification/play_period/fresh_crosscheck.json \
    --json verification/play_period/native_query_fresh.json
```

The SMT queries are written beside the selected classification output. Always
select its matching JSON when checking freshly generated queries. Use `--lib`
to select a shared library other than the default `libz3.so.4`.

Run the independent algebraic check using only Python's standard library:

```bash
python3 check_algebraic_rigidity.py \
    --json verification/play_period/algebraic_rigidity.json
```

These are reproducible computer-assisted certificates, supplemented by an
elementary uniqueness argument for the surviving skeleton. No proof-assistant
formalization is claimed.
