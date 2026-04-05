#pragma once
#include <vector>
#include <stack>
#include <algorithm>
#include <functional>

class TarjanSCC {
public:
    explicit TarjanSCC(int n) : adj_(n) {}

    void add_edge(int u, int v) {
        adj_[u].push_back(v);
    }

    std::vector<std::vector<int>> find_sccs() {
        int n = (int)adj_.size();
        std::vector<int> disc(n, -1), low(n, -1);
        std::vector<bool> on_stack(n, false);
        std::stack<int> st;
        std::vector<std::vector<int>> result;
        int timer = 0;

        std::function<void(int)> dfs = [&](int u) {
            disc[u] = low[u] = timer++;
            st.push(u);
            on_stack[u] = true;

            for (int v : adj_[u]) {
                if (disc[v] == -1) {
                    dfs(v);
                    low[u] = std::min(low[u], low[v]);
                } else {
                    low[u] = std::min(low[u], disc[v]);
                }
            }

            if (low[u] == disc[u]) {
                std::vector<int> component;
                while (true) {
                    int v = st.top(); st.pop();
                    on_stack[v] = false;
                    component.push_back(v);
                    if (v == u) break;
                }
                std::sort(component.begin(), component.end());
                result.push_back(component);
            }
        };

        for (int i = 0; i < n; ++i)
            if (disc[i] == -1) dfs(i);

        std::sort(result.begin(), result.end());
        return result;
    }

private:
    std::vector<std::vector<int>> adj_;
};
