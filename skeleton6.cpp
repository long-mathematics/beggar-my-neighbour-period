// Enumerate all period-six face-only Beggar-My-Neighbour itineraries.
// Output format: initial_A_face_count, six-bit winner word (0=A,1=B),
// six face counts, then the resulting permutation of 16 original face slots.
//
// The initial leader equals the final winner and is normalized to A.
// Winner words are reduced by cyclic rotation and player interchange.
// Faces are temporarily labelled 0..15 so the cycle's return permutation
// is exact. Every return-permutation orbit must be monochromatic, with
// four copies of each of the four face ranks.
//
// Compile: c++ -O3 -std=c++20 skeleton6.cpp -o skeleton6
// Run:     ./skeleton6 skeleton6.tsv
//
// The independent Python implementation is prove_minimum.skeletons(6).
#include <algorithm>
#include <array>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>
using namespace std;

using WinnerWord = array<int, 6>;

vector<WinnerWord> winner_representatives() {
    set<WinnerWord> words;
    for (int mask = 1; mask < 63; ++mask) {  // exclude constant winners
        vector<WinnerWord> images;
        for (int exchange = 0; exchange < 2; ++exchange) {
            for (int rotation = 0; rotation < 6; ++rotation) {
                WinnerWord w{};
                for (int j = 0; j < 6; ++j) {
                    w[j] = ((mask >> ((rotation + j) % 6)) & 1) ^ exchange;
                }
                if (w[5] == 0) images.push_back(w);
            }
        }
        if (!images.empty()) words.insert(*max_element(images.begin(), images.end()));
    }
    return vector<WinnerWord>(words.rbegin(), words.rend());
}

int rank_colorings(const vector<int>& cycle_sizes) {
    map<array<int, 4>, int> dp;
    dp[{0, 0, 0, 0}] = 1;
    for (int length : cycle_sizes) {
        map<array<int, 4>, int> next;
        for (const auto& [counts, ways] : dp) {
            for (int color = 0; color < 4; ++color) {
                auto new_counts = counts;
                if (new_counts[color] + length <= 4) {
                    new_counts[color] += length;
                    next[new_counts] += ways;
                }
            }
        }
        dp = move(next);
        if (dp.empty()) break;
    }
    return dp[{4, 4, 4, 4}];
}

int main(int argc, char** argv) {
    if (argc != 2) {
        cerr << "Usage: " << argv[0] << " skeleton6.tsv\n";
        return 2;
    }
    ofstream out(argv[1]);
    if (!out) return 3;
    long long total = 0, rank_assignments = 0;
    map<string, long long> by_winner;
    map<vector<int>, int> coloring_cache;
    const auto words = winner_representatives();
    if (words.size() != 7) abort();

    for (const auto& winners : words) {
        string word;
        for (int winner : winners) word += char('0' + winner);
        // The final face transfer is forced by total face balance.
        for (int packed = 0; packed < (1 << 15); ++packed) {
            int k[6];
            int balance = 0;
            for (int i = 0; i < 5; ++i) {
                k[i] = (packed >> (3 * i)) & 7;
                balance += k[i] * (winners[i] == 0 ? 1 : -1);
            }
            k[5] = -balance;  // final winner is A
            if (k[5] < 0 || k[5] > 7) continue;

            for (int parity = 0; parity < 64; ++parity) {
                int faces_per_trick[6];
                bool legal = true;
                for (int i = 0; i < 6; ++i) {
                    faces_per_trick[i] = 2 * k[i] + ((parity >> i) & 1);
                    if (faces_per_trick[i] < 1 || faces_per_trick[i] > 15)
                        legal = false;
                }
                if (!legal) continue;

                for (int initial_a = 1; initial_a < 16; ++initial_a) {
                    // Neither hand may lose its last face in a periodic game.
                    int face_count_a = initial_a;
                    bool possible = true;
                    for (int i = 0; i < 6; ++i) {
                        face_count_a += (winners[i] == 0 ? k[i] : -k[i]);
                        if (face_count_a <= 0 || face_count_a >= 16) {
                            possible = false;
                            break;
                        }
                    }
                    if (!possible || face_count_a != initial_a) continue;

                    // Two length-32 ring buffers for the temporarily distinct
                    // 16 face cards. During a trick, the owner of face j is
                    // winner XOR parity of distance from the final face.
                    int ring[2][32]{};
                    int head[2]{0, 0};
                    int length[2]{initial_a, 16 - initial_a};
                    for (int j = 0; j < initial_a; ++j) ring[0][j] = j;
                    for (int j = initial_a; j < 16; ++j)
                        ring[1][j - initial_a] = j;

                    for (int trick = 0; trick < 6 && possible; ++trick) {
                        int pile[16]{};
                        const int m = faces_per_trick[trick];
                        for (int j = 0; j < m; ++j) {
                            int player = winners[trick] ^ ((m - 1 - j) & 1);
                            if (length[player] == 0) {
                                possible = false;
                                break;
                            }
                            pile[j] = ring[player][head[player]];
                            head[player] = (head[player] + 1) % 32;
                            --length[player];
                        }
                        if (!possible) break;
                        int winner = winners[trick];
                        for (int j = 0; j < m; ++j) {
                            ring[winner][(head[winner] + length[winner]) % 32] = pile[j];
                            ++length[winner];
                        }
                    }
                    if (!possible || length[0] != initial_a ||
                        length[1] != 16 - initial_a) continue;

                    vector<int> permutation;
                    for (int player = 0; player < 2; ++player)
                        for (int j = 0; j < length[player]; ++j)
                            permutation.push_back(ring[player][(head[player] + j) % 32]);
                    if (permutation.size() != 16) abort();
                    vector<bool> seen(16, false);
                    vector<int> orbit_sizes;
                    for (int j = 0; j < 16; ++j) {
                        if (seen[j]) continue;
                        int n = 0, next = j;
                        while (!seen[next]) {
                            seen[next] = true;
                            next = permutation[next];
                            ++n;
                        }
                        orbit_sizes.push_back(n);
                    }
                    sort(orbit_sizes.rbegin(), orbit_sizes.rend());
                    if (orbit_sizes.front() > 4) continue;
                    int colors;
                    if (auto it = coloring_cache.find(orbit_sizes);
                        it != coloring_cache.end()) {
                        colors = it->second;
                    } else {
                        colors = rank_colorings(orbit_sizes);
                        coloring_cache[orbit_sizes] = colors;
                    }
                    if (colors == 0) continue;
                    ++total;
                    rank_assignments += colors;
                    ++by_winner[word];
                    out << initial_a << ' ' << word << ' ';
                    for (int m : faces_per_trick) out << m << ' ';
                    for (int i = 0; i < 16; ++i)
                        out << permutation[i] << (i == 15 ? '\n' : ' ');
                }
            }
        }
        cerr << "Winner " << word << ": " << by_winner[word] << " skeletons\n";
    }
    cerr << "Total " << total << " skeletons, " << rank_assignments
         << " rank colorings\n";
    if (total != 21407 || rank_assignments != 2688096) return 4;
    return 0;
}
