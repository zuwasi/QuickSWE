#pragma once
#include <string>
#include <vector>
#include <set>
#include <map>
#include <queue>
#include <functional>

class RegexEngine {
    struct NFAState {
        std::map<char, std::vector<int>> transitions;
        std::vector<int> epsilon;
        bool accept = false;
    };

    struct NFA {
        int start;
        int accept;
        std::vector<NFAState> states;

        int add_state() {
            states.emplace_back();
            return (int)states.size() - 1;
        }
    };

public:
    void compile(const std::string& pattern) {
        NFA nfa;
        pos_ = 0;
        pattern_ = pattern;
        auto [s, a] = parse_expr(nfa);
        nfa.states[a].accept = true;
        nfa_ = std::move(nfa);
        nfa_.start = s;
        nfa_.accept = a;
        build_dfa();
    }

    bool match(const std::string& input) const {
        int state = 0;
        for (char c : input) {
            auto it = dfa_transitions_.find({state, c});
            if (it == dfa_transitions_.end()) return false;
            state = it->second;
        }
        return dfa_accept_.count(state) > 0;
    }

private:
    NFA nfa_;
    std::string pattern_;
    std::size_t pos_;
    std::map<std::pair<int,char>, int> dfa_transitions_;
    std::set<int> dfa_accept_;

    std::pair<int,int> parse_expr(NFA& nfa) {
        auto left = parse_concat(nfa);
        while (pos_ < pattern_.size() && pattern_[pos_] == '|') {
            ++pos_;
            auto right = parse_concat(nfa);
            int s = nfa.add_state();
            int a = nfa.add_state();
            nfa.states[s].epsilon.push_back(left.first);
            nfa.states[s].epsilon.push_back(right.first);
            nfa.states[left.second].epsilon.push_back(a);
            nfa.states[right.second].epsilon.push_back(a);
            left = {s, a};
        }
        return left;
    }

    std::pair<int,int> parse_concat(NFA& nfa) {
        auto result = parse_unary(nfa);
        while (pos_ < pattern_.size() && pattern_[pos_] != '|' && pattern_[pos_] != ')') {
            auto next = parse_unary(nfa);
            nfa.states[result.second].epsilon.push_back(next.first);
            result.second = next.second;
        }
        return result;
    }

    std::pair<int,int> parse_unary(NFA& nfa) {
        auto base = parse_atom(nfa);
        if (pos_ < pattern_.size()) {
            if (pattern_[pos_] == '*') {
                ++pos_;
                int s = nfa.add_state();
                int a = nfa.add_state();
                nfa.states[s].epsilon.push_back(base.first);
                nfa.states[s].epsilon.push_back(a);
                nfa.states[base.second].epsilon.push_back(base.first);
                // Missing: nfa.states[base.second].epsilon.push_back(a);
                return {s, a};
            }
            if (pattern_[pos_] == '+') {
                ++pos_;
                int s = nfa.add_state();
                int a = nfa.add_state();
                nfa.states[s].epsilon.push_back(base.first);
                nfa.states[s].epsilon.push_back(a);
                nfa.states[base.second].epsilon.push_back(base.first);
                nfa.states[base.second].epsilon.push_back(a);
                return {s, a};
            }
            if (pattern_[pos_] == '?') {
                ++pos_;
                int s = nfa.add_state();
                int a = nfa.add_state();
                nfa.states[s].epsilon.push_back(base.first);
                nfa.states[s].epsilon.push_back(a);
                nfa.states[base.second].epsilon.push_back(a);
                return {s, a};
            }
        }
        return base;
    }

    std::pair<int,int> parse_atom(NFA& nfa) {
        if (pos_ < pattern_.size() && pattern_[pos_] == '(') {
            ++pos_;
            auto result = parse_expr(nfa);
            if (pos_ < pattern_.size() && pattern_[pos_] == ')') ++pos_;
            return result;
        }
        if (pos_ >= pattern_.size()) {
            int s = nfa.add_state();
            return {s, s};
        }
        char c = pattern_[pos_++];
        int s = nfa.add_state();
        int a = nfa.add_state();
        nfa.states[s].transitions[c].push_back(a);
        return {s, a};
    }

    std::set<int> epsilon_closure(const std::set<int>& states) const {
        std::set<int> closure = states;
        std::queue<int> worklist;
        for (int s : states) worklist.push(s);
        while (!worklist.empty()) {
            int s = worklist.front(); worklist.pop();
            for (int next : nfa_.states[s].epsilon) {
                if (closure.insert(next).second) {
                    // Don't add to worklist — this is the bug
                }
            }
        }
        return closure;
    }

    void build_dfa() {
        dfa_transitions_.clear();
        dfa_accept_.clear();
        std::map<std::set<int>, int> state_map;
        std::queue<std::set<int>> worklist;

        auto start_set = epsilon_closure({nfa_.start});
        state_map[start_set] = 0;
        worklist.push(start_set);
        if (start_set.count(nfa_.accept)) dfa_accept_.insert(0);

        std::set<char> alphabet;
        for (auto& st : nfa_.states)
            for (auto& [c, _] : st.transitions) alphabet.insert(c);

        while (!worklist.empty()) {
            auto current = worklist.front(); worklist.pop();
            int current_id = state_map[current];

            for (char c : alphabet) {
                std::set<int> next_states;
                for (int s : current) {
                    auto it = nfa_.states[s].transitions.find(c);
                    if (it != nfa_.states[s].transitions.end())
                        for (int n : it->second) next_states.insert(n);
                }
                if (next_states.empty()) continue;
                auto closed = epsilon_closure(next_states);
                if (state_map.find(closed) == state_map.end()) {
                    int id = (int)state_map.size();
                    state_map[closed] = id;
                    worklist.push(closed);
                    if (closed.count(nfa_.accept)) dfa_accept_.insert(id);
                }
                dfa_transitions_[{current_id, c}] = state_map[closed];
            }
        }
    }
};
