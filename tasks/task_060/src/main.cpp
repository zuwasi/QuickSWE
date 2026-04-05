#include "variadic.hpp"
#include <iostream>
#include <string>

void test_sum_all() {
    auto r = sum_all(1, 2, 3, 4);
    bool ok = (r == 10);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_sum_all" << std::endl;
}

void test_all_of_true() {
    bool r = all_of(true, true, true);
    std::cout << (r ? "PASS" : "FAIL") << ": test_all_of_true" << std::endl;
}

void test_all_of_false() {
    bool r = all_of(true, false, true);
    bool ok = (r == false);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_all_of_false" << std::endl;
}

void test_any_of_true() {
    bool r = any_of(false, false, true);
    bool ok = (r == true);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_any_of_true" << std::endl;
}

void test_any_of_false() {
    bool r = any_of(false, false, false);
    bool ok = (r == false);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_any_of_false" << std::endl;
}

void test_transform_reduce() {
    auto r = transform_reduce([](int x) { return x * x; }, 1, 2, 3);
    bool ok = (r == 14);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_transform_reduce" << std::endl;
}

void test_apply_to_each() {
    auto r = apply_to_each([](int x) { return x * 2; }, 1, 2, 3);
    bool ok = (r.size() == 3) && (r[0] == 2) && (r[1] == 4) && (r[2] == 6);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_apply_to_each" << std::endl;
}

void test_count_if() {
    int r = count_if([](int x) { return x > 3; }, 1, 2, 5, 4, 3);
    bool ok = (r == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_count_if" << std::endl;
}

void test_min_of() {
    auto r = min_of(5, 3, 7, 1, 4);
    bool ok = (r == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_min_of" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_sum_all")          test_sum_all();
    else if (test == "test_all_of_true")      test_all_of_true();
    else if (test == "test_all_of_false")     test_all_of_false();
    else if (test == "test_any_of_true")      test_any_of_true();
    else if (test == "test_any_of_false")     test_any_of_false();
    else if (test == "test_transform_reduce") test_transform_reduce();
    else if (test == "test_apply_to_each")    test_apply_to_each();
    else if (test == "test_count_if")         test_count_if();
    else if (test == "test_min_of")           test_min_of();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
