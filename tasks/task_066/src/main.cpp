#include "tarjan.hpp"
#include <iostream>
#include <string>
#include <set>

void test_simple_cycle() {
    TarjanSCC g(3);
    g.add_edge(0, 1); g.add_edge(1, 2); g.add_edge(2, 0);
    auto sccs = g.find_sccs();
    bool ok = (sccs.size() == 1) && (sccs[0].size() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_simple_cycle" << std::endl;
}

void test_dag() {
    TarjanSCC g(4);
    g.add_edge(0, 1); g.add_edge(1, 2); g.add_edge(2, 3);
    auto sccs = g.find_sccs();
    bool ok = (sccs.size() == 4);
    for (auto& scc : sccs) if (scc.size() != 1) ok = false;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_dag" << std::endl;
}

void test_two_sccs() {
    TarjanSCC g(6);
    // SCC1: 0-1-2-0
    g.add_edge(0, 1); g.add_edge(1, 2); g.add_edge(2, 0);
    // SCC2: 3-4-3
    g.add_edge(3, 4); g.add_edge(4, 3);
    // Cross: 2->3 (not in any cycle)
    g.add_edge(2, 3);
    // Node 5 alone
    g.add_edge(4, 5);
    auto sccs = g.find_sccs();
    bool ok = (sccs.size() == 4);
    // Check SCC sizes: should have one of size 3, one of size 2, two of size 1
    std::set<int> sizes;
    for (auto& scc : sccs) sizes.insert((int)scc.size());
    ok = ok && sizes.count(3) && sizes.count(2) && sizes.count(1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_two_sccs" << std::endl;
}

void test_cross_edge_no_merge() {
    // 0->1->2->0 (SCC), 0->3->4->5->3 (SCC), should be 2 SCCs + no others merged
    TarjanSCC g(6);
    g.add_edge(0, 1); g.add_edge(1, 2); g.add_edge(2, 0);
    g.add_edge(0, 3); g.add_edge(3, 4); g.add_edge(4, 5); g.add_edge(5, 3);
    auto sccs = g.find_sccs();
    bool ok = (sccs.size() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_cross_edge_no_merge" << std::endl;
}

void test_self_loop() {
    TarjanSCC g(3);
    g.add_edge(0, 0);
    g.add_edge(1, 2);
    auto sccs = g.find_sccs();
    bool ok = (sccs.size() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_self_loop" << std::endl;
}

void test_single_node() {
    TarjanSCC g(1);
    auto sccs = g.find_sccs();
    bool ok = (sccs.size() == 1) && (sccs[0].size() == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_single_node" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_simple_cycle")         test_simple_cycle();
    else if (test == "test_dag")                  test_dag();
    else if (test == "test_two_sccs")             test_two_sccs();
    else if (test == "test_cross_edge_no_merge")  test_cross_edge_no_merge();
    else if (test == "test_self_loop")            test_self_loop();
    else if (test == "test_single_node")          test_single_node();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
