// Independent check of the bounded face-itinerary candidate set.
// Enumerate face counts using only scalar hand sizes; replay labelled queues
// only at leaves. No future face-balance or rank-cost pruning in the DFS.
#include <algorithm>
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>
using namespace std;
int P, B, initial;
vector<int> w, m, suffix;
ofstream output;
uint64_t nodes=0, leaves=0, kept=0;
map<vector<pair<int,int>>,int> penalty_cache;

vector<vector<int>> patterns(int p) {
    set<vector<int>> answers;
    for (int bits=1; bits<(1<<p)-1; ++bits) {
        vector<int> candidate(p);
        for (int j=0; j<p; ++j) candidate[j]=(bits>>j)&1;
        if (candidate.back()!=0) continue;
        bool maximal=true;
        for (int s=0;s<p && maximal;++s) for(int c=0;c<2 && maximal;++c) {
            vector<int> other(p);
            for(int j=0;j<p;++j) other[j]=candidate[(j+s)%p]^c;
            if(other.back()==0 && other>candidate) maximal=false;
        }
        if(maximal) answers.insert(candidate);
    }
    return vector<vector<int>>(answers.begin(),answers.end());
}

int min_penalties(vector<pair<int,int>> components) {
    sort(components.begin(),components.end());
    auto found=penalty_cache.find(components);
    if(found!=penalty_cache.end()) return found->second;
    // A separate capacity-state map implementation of the four rank bins.
    map<array<int,4>,int> dp; dp[{0,0,0,0}]=0;
    for(auto component:components) {
        map<array<int,4>,int> next;
        for(auto state:dp) for(int rank=1;rank<=4;++rank) {
            auto counts=state.first;
            counts[rank-1]+=component.first;
            if(counts[rank-1]>4) continue;
            int cost=state.second+rank*component.second;
            auto it=next.find(counts);
            if(it==next.end() || cost<it->second) next[counts]=cost;
        }
        dp=move(next);
    }
    auto it=dp.find({4,4,4,4});
    int cost=it==dp.end()?100000:it->second;
    penalty_cache[components]=cost;
    return cost;
}

void replay(int cost) {
    ++leaves;
    deque<int> hand[2];
    for(int i=0;i<initial;++i) hand[0].push_back(i);
    for(int i=initial;i<16;++i) hand[1].push_back(i);
    array<int,16> terminal{};
    for(int t=0;t<P;++t) {
        vector<int> pile;
        int player=(m[t]%2==1)?w[t]:1-w[t];
        for(int j=0;j<m[t];++j) {
            if(hand[player].empty()) abort();
            pile.push_back(hand[player].front());
            hand[player].pop_front();
            player=1-player;
        }
        terminal[pile.back()]++;
        for(int card:pile) hand[w[t]].push_back(card);
    }
    vector<int> permutation(hand[0].begin(),hand[0].end());
    permutation.insert(permutation.end(),hand[1].begin(),hand[1].end());
    array<bool,16> visited{};
    vector<pair<int,int>> components;
    for(int i=0;i<16;++i) if(!visited[i]) {
        int length=0, count=0, j=i;
        do {
            if(visited[j]) abort();
            visited[j]=true; ++length; count+=terminal[j];
            j=permutation[j];
        } while(j!=i);
        if(length>4) return;
        components.push_back({length,count});
    }
    if(cost-P+min_penalties(components)>B) return;
    ++kept;
    output<<initial<<' ';
    for(int x:w) output<<x;
    output<<' ';
    for(int x:m) output<<x<<' ';
    for(int j=0;j<16;++j) output<<permutation[j]<<(j==15?'\n':' ');
}

void extend(int t,int a,int cost) {
    ++nodes;
    if(t==P) { if(a==initial) replay(cost); return; }
    for(int faces=1;faces<=15;++faces) {
        int winner=w[t];
        int first=(faces%2==1)?winner:1-winner;
        int previous=t==0?0:w[t-1];
        int newcost=cost+faces+1+(first!=previous);
        if(newcost+suffix[t+1]>B) continue;
        int k=faces/2, e=faces%2;
        int own=winner==0?a:16-a;
        int other=16-own;
        if(k+e>own || k>=other) continue;
        int newa=a+(winner==0?k:-k);
        m[t]=faces;
        extend(t+1,newa,newcost);
    }
}

int main(int argc,char**argv) {
    if(argc!=4) {
        cerr<<"Usage: "<<argv[0]<<" period budget output\n";
        return 2;
    }
    P=stoi(argv[1]); B=stoi(argv[2]);
    if(P<2 || P>18 || B<0) {
        cerr<<"Expected 2<=period<=18 and a nonnegative budget\n";
        return 2;
    }
    output.open(argv[3]);
    if(!output) return 3;
    m.resize(P); suffix.resize(P+1);
    for(auto word:patterns(P)) {
        w=move(word);suffix[P]=0;
        for(int t=P-1;t>=0;--t)
            suffix[t]=suffix[t+1]+2+(w[t]!=(t==0?0:w[t-1]));
        if(suffix[0]>B) continue;
        for(initial=1;initial<16;++initial) extend(0,initial,0);
    }
    cerr<<"period="<<P<<" budget="<<B<<" nodes="<<nodes
        <<" leaves="<<leaves<<" kept="<<kept<<'\n';
    output.flush();
    return output ? 0 : 3;
}
