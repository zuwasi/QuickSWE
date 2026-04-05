#include "skiplist.hpp"
#include <iostream>
#include <string>

void test_insert_search() {
    SkipList<int> sl(123);
    for (int i = 1; i <= 20; ++i) sl.insert(i);
    bool ok = true;
    for (int i = 1; i <= 20; ++i) if (!sl.search(i)) ok = false;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_search" << std::endl;
}

void test_multilevel() {
    SkipList<int> sl(42);
    for (int i = 1; i <= 50; ++i) sl.insert(i);
    bool ok = (sl.current_level() > 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_multilevel" << std::endl;
}

void test_forward_pointers() {
    SkipList<int> sl(99);
    sl.insert(10); sl.insert(20); sl.insert(30); sl.insert(5); sl.insert(15);
    bool ok = sl.search(5) && sl.search(15) && sl.search(30);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_forward_pointers" << std::endl;
}

void test_remove_updates_level() {
    SkipList<int> sl(42);
    for (int i = 1; i <= 30; ++i) sl.insert(i);
    for (int i = 1; i <= 30; ++i) sl.remove(i);
    sl.insert(100);
    bool ok = sl.search(100) && (sl.size() == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_remove_updates_level" << std::endl;
}

void test_to_vector_sorted() {
    SkipList<int> sl(77);
    sl.insert(5); sl.insert(1); sl.insert(3); sl.insert(7);
    auto v = sl.to_vector();
    bool ok = (v.size() == 4) && (v[0]==1) && (v[1]==3) && (v[2]==5) && (v[3]==7);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_to_vector_sorted" << std::endl;
}

void test_size() {
    SkipList<int> sl(55);
    sl.insert(1); sl.insert(2); sl.insert(3);
    sl.remove(2);
    bool ok = (sl.size() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_size" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_insert_search")       test_insert_search();
    else if (test == "test_multilevel")           test_multilevel();
    else if (test == "test_forward_pointers")    test_forward_pointers();
    else if (test == "test_remove_updates_level") test_remove_updates_level();
    else if (test == "test_to_vector_sorted")    test_to_vector_sorted();
    else if (test == "test_size")                test_size();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
