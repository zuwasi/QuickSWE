#include "hamtrie.hpp"
#include <iostream>
#include <string>

void test_insert_find() {
    HAMTrie t;
    auto t2 = t.insert("hello", 1);
    auto t3 = t2.insert("world", 2);
    bool ok = t3.find("hello").value() == 1 && t3.find("world").value() == 2;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_find" << std::endl;
}

void test_persistence_insert() {
    HAMTrie t;
    auto v1 = t.insert("a", 1);
    auto v2 = v1.insert("b", 2);
    // v1 should NOT have "b"
    bool ok = v1.contains("a") && !v1.contains("b") && v2.contains("a") && v2.contains("b");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_persistence_insert" << std::endl;
}

void test_persistence_remove() {
    HAMTrie t;
    auto v1 = t.insert("a", 1).insert("b", 2).insert("c", 3);
    auto v2 = v1.remove("b");
    // v1 should still have "b"
    bool ok = v1.contains("b") && !v2.contains("b") && v2.contains("a") && v2.contains("c");
    ok = ok && (v1.size() == 3) && (v2.size() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_persistence_remove" << std::endl;
}

void test_overwrite() {
    HAMTrie t;
    auto v1 = t.insert("key", 10);
    auto v2 = v1.insert("key", 20);
    bool ok = v1.find("key").value() == 10 && v2.find("key").value() == 20;
    ok = ok && (v2.size() == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_overwrite" << std::endl;
}

void test_many_keys() {
    HAMTrie t;
    for (int i = 0; i < 20; ++i) {
        t = t.insert("key" + std::to_string(i), i);
    }
    bool ok = (t.size() == 20);
    for (int i = 0; i < 20 && ok; ++i) {
        auto v = t.find("key" + std::to_string(i));
        if (!v.has_value() || v.value() != i) ok = false;
    }
    std::cout << (ok ? "PASS" : "FAIL") << ": test_many_keys" << std::endl;
}

void test_empty() {
    HAMTrie t;
    bool ok = (t.size() == 0) && !t.contains("x");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_empty" << std::endl;
}

void test_all_entries() {
    HAMTrie t;
    t = t.insert("b", 2).insert("a", 1).insert("c", 3);
    auto entries = t.all_entries();
    bool ok = (entries.size() == 3) && entries[0].first == "a" && entries[2].first == "c";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_all_entries" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_insert_find")         test_insert_find();
    else if (test == "test_persistence_insert")  test_persistence_insert();
    else if (test == "test_persistence_remove")  test_persistence_remove();
    else if (test == "test_overwrite")           test_overwrite();
    else if (test == "test_many_keys")           test_many_keys();
    else if (test == "test_empty")               test_empty();
    else if (test == "test_all_entries")         test_all_entries();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
