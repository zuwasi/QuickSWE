#include "hashmap.hpp"
#include <iostream>
#include <string>

void test_basic_insert_get() {
    HashMap<std::string, int> map(8);
    map.insert("a", 1);
    map.insert("b", 2);
    auto ra = map.get("a");
    auto rb = map.get("b");
    bool ok = ra.first && ra.second == 1 && rb.first && rb.second == 2;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_insert_get" << std::endl;
}

void test_lookup_after_delete() {
    HashMap<int, int> map(4);
    map.insert(0, 100);
    map.insert(4, 200);
    map.insert(8, 300);
    map.remove(0);
    auto val = map.get(4);
    bool ok = val.first && val.second == 200;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_lookup_after_delete" << std::endl;
}

void test_lookup_chain_after_delete() {
    HashMap<int, int> map(4);
    map.insert(0, 10);
    map.insert(4, 20);
    map.insert(8, 30);
    map.remove(4);
    auto val = map.get(8);
    bool ok = val.first && val.second == 30;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_lookup_chain_after_delete" << std::endl;
}

void test_reinsert_after_delete() {
    HashMap<int, int> map(8);
    map.insert(0, 100);
    map.insert(8, 200);
    map.remove(0);
    map.insert(8, 999);
    auto val = map.get(8);
    bool ok = (map.size() == 1) && val.first && (val.second == 999);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_reinsert_after_delete" << std::endl;
}

void test_contains() {
    HashMap<std::string, int> map(8);
    map.insert("x", 42);
    bool ok = map.contains("x") && !map.contains("y");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_contains" << std::endl;
}

void test_overwrite() {
    HashMap<std::string, int> map(8);
    map.insert("k", 1);
    map.insert("k", 2);
    auto val = map.get("k");
    bool ok = (map.size() == 1) && val.first && (val.second == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_overwrite" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_basic_insert_get")        test_basic_insert_get();
    else if (test == "test_lookup_after_delete")      test_lookup_after_delete();
    else if (test == "test_lookup_chain_after_delete") test_lookup_chain_after_delete();
    else if (test == "test_reinsert_after_delete")    test_reinsert_after_delete();
    else if (test == "test_contains")                 test_contains();
    else if (test == "test_overwrite")                test_overwrite();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
