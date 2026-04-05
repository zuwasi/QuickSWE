#include "vector.hpp"
#include <iostream>
#include <string>

void test_erase_single() {
    Vector<int> v = {1, 2, 3, 4, 5};
    auto it = v.erase(v.begin() + 2);  // erase 3
    // v should be {1,2,4,5}, it should point to 4
    bool ok = (v.size() == 4) && (*it == 4) && v[0]==1 && v[1]==2 && v[2]==4 && v[3]==5;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_erase_single" << std::endl;
}

void test_erase_loop() {
    Vector<int> v = {1, 2, 3, 4, 5};
    // Erase all even numbers
    auto it = v.begin();
    while (it != v.end()) {
        if (*it % 2 == 0) {
            it = v.erase(it);
        } else {
            ++it;
        }
    }
    bool ok = (v.size() == 3) && (v[0]==1) && (v[1]==3) && (v[2]==5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_erase_loop" << std::endl;
}

void test_erase_range() {
    Vector<int> v = {1, 2, 3, 4, 5};
    auto it = v.erase(v.begin() + 1, v.begin() + 3);  // erase 2,3
    bool ok = (v.size() == 3) && (*it == 4) && v[0]==1 && v[1]==4 && v[2]==5;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_erase_range" << std::endl;
}

void test_erase_range_all() {
    Vector<int> v = {1, 2, 3};
    v.erase(v.begin(), v.end());
    bool ok = (v.size() == 0) && v.empty();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_erase_range_all" << std::endl;
}

void test_erase_first() {
    Vector<int> v = {10, 20, 30};
    auto it = v.erase(v.begin());
    bool ok = (v.size() == 2) && (*it == 20);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_erase_first" << std::endl;
}

void test_erase_last() {
    Vector<int> v = {10, 20, 30};
    auto it = v.erase(v.begin() + 2);
    bool ok = (v.size() == 2) && (it == v.end());
    std::cout << (ok ? "PASS" : "FAIL") << ": test_erase_last" << std::endl;
}

void test_push_after_erase() {
    Vector<int> v = {1, 2, 3};
    v.erase(v.begin());
    v.push_back(4);
    bool ok = (v.size() == 3) && v[0]==2 && v[1]==3 && v[2]==4;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_push_after_erase" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_erase_single")     test_erase_single();
    else if (test == "test_erase_loop")       test_erase_loop();
    else if (test == "test_erase_range")      test_erase_range();
    else if (test == "test_erase_range_all")  test_erase_range_all();
    else if (test == "test_erase_first")      test_erase_first();
    else if (test == "test_erase_last")       test_erase_last();
    else if (test == "test_push_after_erase") test_push_after_erase();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
