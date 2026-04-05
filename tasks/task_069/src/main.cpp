#include "gc.hpp"
#include <iostream>
#include <string>

void test_basic_collect() {
    GarbageCollector gc;
    int a = gc.allocate(10);
    int b = gc.allocate(20);
    gc.set_root(a);
    gc.collect();
    bool ok = (gc.heap_size() == 1) && (gc.dereference(a) == 10);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_collect" << std::endl;
}

void test_transitive_reachability() {
    GarbageCollector gc;
    int a = gc.allocate(1);
    int b = gc.allocate(2);
    int c = gc.allocate(3);
    int d = gc.allocate(4);
    gc.add_reference(a, b);
    gc.add_reference(b, c);
    // d is unreachable
    gc.set_root(a);
    gc.collect();
    bool ok = (gc.heap_size() == 3);
    ok = ok && (gc.dereference(a) == 1) && (gc.dereference(b) == 2) && (gc.dereference(c) == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_transitive_reachability" << std::endl;
}

void test_cycle_collection() {
    GarbageCollector gc;
    int a = gc.allocate(1);
    int b = gc.allocate(2);
    gc.add_reference(a, b);
    gc.add_reference(b, a);
    gc.set_root(a);
    gc.collect();
    bool ok = (gc.heap_size() == 2);
    gc.remove_root(a);
    gc.collect();
    ok = ok && (gc.heap_size() == 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_cycle_collection" << std::endl;
}

void test_refs_after_compact() {
    GarbageCollector gc;
    int a = gc.allocate(10);
    int b = gc.allocate(20);
    int c = gc.allocate(30);
    gc.add_reference(a, b);
    gc.add_reference(b, c);
    gc.set_root(a);
    gc.collect();
    gc.compact();
    auto refs_a = gc.get_refs(a);
    bool ok = refs_a.count(b) && gc.get_refs(b).count(c);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_refs_after_compact" << std::endl;
}

void test_multiple_cycles() {
    GarbageCollector gc;
    int a = gc.allocate(1);
    int b = gc.allocate(2);
    int c = gc.allocate(3);
    gc.add_reference(a, b);
    gc.set_root(a);
    gc.collect();
    // a,b survive
    int d = gc.allocate(4);
    gc.add_reference(a, d);
    gc.collect();
    auto ids = gc.all_live_ids();
    bool ok = (ids.size() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_multiple_cycles" << std::endl;
}

void test_no_roots_collect_all() {
    GarbageCollector gc;
    gc.allocate(1); gc.allocate(2); gc.allocate(3);
    gc.collect();
    bool ok = (gc.heap_size() == 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_no_roots_collect_all" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_basic_collect")           test_basic_collect();
    else if (test == "test_transitive_reachability") test_transitive_reachability();
    else if (test == "test_cycle_collection")        test_cycle_collection();
    else if (test == "test_refs_after_compact")      test_refs_after_compact();
    else if (test == "test_multiple_cycles")         test_multiple_cycles();
    else if (test == "test_no_roots_collect_all")    test_no_roots_collect_all();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
