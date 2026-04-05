#include "concurrent_map.hpp"
#include <iostream>
#include <string>

void test_insert_find() {
    ConcurrentMap<std::string, int> m(4);
    m.insert("a", 1);
    m.insert("b", 2);
    auto va = m.find("a");
    auto vb = m.find("b");
    bool ok = va.has_value() && va.value() == 1 && vb.has_value() && vb.value() == 2;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_find" << std::endl;
}

void test_insert_overwrite() {
    ConcurrentMap<std::string, int> m(4);
    m.insert("key", 10);
    m.insert("key", 20);
    bool ok = (m.find("key").value() == 20) && (m.size() == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_overwrite" << std::endl;
}

void test_remove_then_find() {
    ConcurrentMap<std::string, int> m(4);
    m.insert("x", 42);
    m.remove("x");
    bool ok = !m.find("x").has_value() && (m.size() == 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_remove_then_find" << std::endl;
}

void test_collision_chain() {
    // Use small bucket count to force collisions
    ConcurrentMap<int, int> m(2);
    for (int i = 0; i < 10; ++i) m.insert(i, i * 10);
    bool ok = true;
    for (int i = 0; i < 10; ++i) {
        auto v = m.find(i);
        if (!v.has_value() || v.value() != i * 10) ok = false;
    }
    ok = ok && (m.size() == 10);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_collision_chain" << std::endl;
}

void test_remove_middle_of_chain() {
    ConcurrentMap<int, int> m(1);  // all in same bucket
    m.insert(1, 10); m.insert(2, 20); m.insert(3, 30);
    m.remove(2);
    bool ok = m.find(1).has_value() && !m.find(2).has_value() && m.find(3).has_value();
    ok = ok && (m.size() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_remove_middle_of_chain" << std::endl;
}

void test_all_entries() {
    ConcurrentMap<std::string, int> m(4);
    m.insert("a", 1); m.insert("b", 2);
    auto entries = m.all_entries();
    bool ok = (entries.size() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_all_entries" << std::endl;
}

void test_contains() {
    ConcurrentMap<std::string, int> m(4);
    m.insert("hello", 1);
    bool ok = m.contains("hello") && !m.contains("world");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_contains" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_insert_find")          test_insert_find();
    else if (test == "test_insert_overwrite")     test_insert_overwrite();
    else if (test == "test_remove_then_find")     test_remove_then_find();
    else if (test == "test_collision_chain")      test_collision_chain();
    else if (test == "test_remove_middle_of_chain") test_remove_middle_of_chain();
    else if (test == "test_all_entries")          test_all_entries();
    else if (test == "test_contains")            test_contains();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
