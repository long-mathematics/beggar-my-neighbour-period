// Copyright (c) 2026 Christopher D. Long. MIT license; see LICENSE.
// Enumerate every face-only itinerary fitting an individual-play budget.
// Output: initial A face count, winner word, per-trick face counts, and the
// output-slot-to-input-label permutation of the sixteen face cards.
//
// This implementation follows labelled FIFO queues throughout the search.
// independent_play_skeletons.cpp uses scalar face counts and replays only
// at leaves. verify_unique38.py compares their complete output sets.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>
using namespace std;

struct State {
    array<int, 16> a, b;
    int na, nb;
};

int period, budget, initial_a;
ofstream output;
vector<int> winners, face_counts, terminal_faces;
long long nodes = 0, balanced_leaves = 0, candidates = 0;
map<vector<pair<int, int>>, int> penalty_cache;

vector<vector<int>> winner_representatives() {
    set<vector<int>> representatives;
    for (int mask = 1; mask < (1 << period) - 1; ++mask) {
        vector<int> best;
        for (int exchange = 0; exchange < 2; ++exchange) {
            for (int rotation = 0; rotation < period; ++rotation) {
                vector<int> word;
                for (int j = 0; j < period; ++j)
                    word.push_back(((mask >> ((rotation + j) % period)) & 1) ^ exchange);
                if (word.back() == 0 && word > best) best = move(word);
            }
        }
        representatives.insert(best);
    }
    return vector<vector<int>>(representatives.rbegin(), representatives.rend());
}

int minimum_terminal_penalties(vector<pair<int, int>> orbits) {
    // An orbit has (number of cards, number of times it supplies the final
    // face). Give each orbit one rank, filling four bins of capacity four,
    // and minimize the sum of the terminal payments implied by those ranks.
    sort(orbits.begin(), orbits.end());
    if (auto found = penalty_cache.find(orbits); found != penalty_cache.end())
        return found->second;
    constexpr int infinity = 999;
    array<int, 625> dp, next;
    dp.fill(infinity);
    dp[0] = 0;
    for (auto [length, occurrences] : orbits) {
        next.fill(infinity);
        for (int key = 0; key < 625; ++key) {
            if (dp[key] == infinity) continue;
            int power = 1;
            for (int rank = 1; rank <= 4; ++rank, power *= 5) {
                if (key / power % 5 + length <= 4) {
                    int new_key = key + length * power;
                    next[new_key] = min(next[new_key], dp[key] + rank * occurrences);
                }
            }
        }
        dp = next;
    }
    // Base-five key 624 is (4,4,4,4). Infinity also rejects an uncolorable
    // collection of orbits; every orbit's rank multiplicity must be exact.
    penalty_cache[orbits] = dp[624];
    return dp[624];
}

void emit_if_viable(const State& state, int lower_bound) {
    if (state.na != initial_a) return;
    ++balanced_leaves;
    int permutation[16], orbit_index[16];
    bool seen[16]{};
    for (int i = 0; i < state.na; ++i) permutation[i] = state.a[i];
    for (int i = 0; i < state.nb; ++i) permutation[state.na + i] = state.b[i];
    vector<pair<int, int>> orbits;
    for (int first = 0; first < 16; ++first) {
        if (seen[first]) continue;
        int length = 0, current = first, index = orbits.size();
        do {
            seen[current] = true;
            orbit_index[current] = index;
            ++length;
            current = permutation[current];
        } while (!seen[current]);
        if (length > 4) return;
        orbits.push_back({length, 0});
    }
    for (int face : terminal_faces) ++orbits[orbit_index[face]].second;
    // The search charged one terminal payment per trick. Replace those
    // units by the smallest rank-consistent sum of terminal payments.
    if (lower_bound - period + minimum_terminal_penalties(orbits) > budget) return;
    ++candidates;
    output << initial_a << ' ';
    for (int winner : winners) output << winner;
    output << ' ';
    for (int count : face_counts) output << count << ' ';
    for (int i = 0; i < 16; ++i)
        output << permutation[i] << (i == 15 ? '\n' : ' ');
}

void visit(int depth, const State& state, int lower_bound) {
    ++nodes;
    if (depth == period) {
        emit_if_viable(state, lower_bound);
        return;
    }
    int winner = winners[depth];
    int previous = depth == 0 ? 0 : winners[depth - 1];
    int remaining = period - 1 - depth;
    for (int count = 1; count <= 15; ++count) {
        int first = winner ^ ((count - 1) & 1);
        int offset = first != previous;
        int cost = count + 1 + offset;
        if (lower_bound + cost + 2 * remaining > budget) continue;
        int played_a = count / 2 + (winner == 0 && (count & 1));
        int played_b = count - played_a;
        if (played_a > state.na || played_b > state.nb) continue;
        State next;
        next.na = state.na - played_a;
        next.nb = state.nb - played_b;
        // The loser must retain a face at the completed-trick boundary.
        if ((winner == 0 && next.nb == 0) || (winner == 1 && next.na == 0)) continue;
        for (int i = 0; i < next.na; ++i) next.a[i] = state.a[played_a + i];
        for (int i = 0; i < next.nb; ++i) next.b[i] = state.b[played_b + i];
        int consumed_a = 0, consumed_b = 0, last = -1;
        for (int j = 0; j < count; ++j) {
            int player = winner ^ ((count - 1 - j) & 1);
            int face = player ? state.b[consumed_b++] : state.a[consumed_a++];
            last = face;
            if (winner) next.b[next.nb++] = face;
            else next.a[next.na++] = face;
        }
        int displacement = next.na - initial_a;
        // A future trick transferring k faces costs at least 2*k+1 plays.
        // Correcting the displacement therefore needs at least
        // 2*abs(displacement)+remaining additional plays.
        if (2 * abs(displacement) > budget - lower_bound - cost - remaining) continue;
        if (remaining == 0 && displacement != 0) continue;
        bool future_a = false, future_b = false;
        for (int j = depth + 1; j < period; ++j) {
            future_a |= winners[j] == 0;
            future_b |= winners[j] == 1;
        }
        if ((displacement > 0 && !future_b) || (displacement < 0 && !future_a)) continue;
        face_counts[depth] = count;
        terminal_faces[depth] = last;
        visit(depth + 1, next, lower_bound + cost);
    }
}

int main(int argc, char** argv) {
    if (argc < 4 || argc > 5) {
        cerr << "Usage: " << argv[0] << " period budget output [winner-word]\n";
        return 2;
    }
    period = stoi(argv[1]);
    budget = stoi(argv[2]);
    if (period < 2 || period > 18 || budget < 0) {
        cerr << "Expected 2<=period<=18 and a nonnegative budget\n";
        return 2;
    }
    output.open(argv[3]);
    if (!output) return 3;
    face_counts.resize(period);
    terminal_faces.resize(period);
    auto started = chrono::steady_clock::now();
    for (const auto& word : winner_representatives()) {
        string printed_word;
        for (int winner : word) printed_word += char('0' + winner);
        if (argc == 5 && printed_word != argv[4]) continue;
        winners = word;
        long long before = candidates;
        int changes = 0;
        for (int j = 0; j < period; ++j)
            changes += winners[j] != winners[(j + period - 1) % period];
        if (2 * period + changes > budget) continue;
        for (initial_a = 1; initial_a < 16; ++initial_a) {
            State initial;
            initial.na = initial_a;
            initial.nb = 16 - initial_a;
            for (int j = 0; j < initial.na; ++j) initial.a[j] = j;
            for (int j = 0; j < initial.nb; ++j) initial.b[j] = j + initial_a;
            visit(0, initial, 0);
        }
        cerr << "winner " << printed_word << " candidates " << candidates - before
             << " total " << candidates << " nodes " << nodes << " seconds "
             << chrono::duration<double>(chrono::steady_clock::now() - started).count() << '\n';
    }
    cerr << "FINAL period=" << period << " budget=" << budget << " candidates=" << candidates
         << " nodes=" << nodes << " leaves=" << balanced_leaves << '\n';
    output.flush();
    return output ? 0 : 3;
}
