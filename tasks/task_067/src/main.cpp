#include "pratt_parser.hpp"
#include <iostream>
#include <string>
#include <cmath>

bool close(double a, double b) { return std::abs(a - b) < 1e-9; }

void test_simple_add() {
    PrattParser p;
    bool ok = close(p.parse("1 + 2"), 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_simple_add" << std::endl;
}

void test_precedence() {
    PrattParser p;
    bool ok = close(p.parse("2 + 3 * 4"), 14);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_precedence" << std::endl;
}

void test_power_right_assoc() {
    PrattParser p;
    // 2^3^2 should be 2^(3^2) = 2^9 = 512
    bool ok = close(p.parse("2 ^ 3 ^ 2"), 512);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_power_right_assoc" << std::endl;
}

void test_unary_minus() {
    PrattParser p;
    bool ok = close(p.parse("-3 + 4"), 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_unary_minus" << std::endl;
}

void test_parens() {
    PrattParser p;
    bool ok = close(p.parse("(2 + 3) * 4"), 20);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_parens" << std::endl;
}

void test_complex() {
    PrattParser p;
    // 1 + 2 * 3 - 4 / 2 = 1 + 6 - 2 = 5
    bool ok = close(p.parse("1 + 2 * 3 - 4 / 2"), 5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_complex" << std::endl;
}

void test_nested_parens() {
    PrattParser p;
    bool ok = close(p.parse("((2 + 3))"), 5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_nested_parens" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_simple_add")         test_simple_add();
    else if (test == "test_precedence")         test_precedence();
    else if (test == "test_power_right_assoc")  test_power_right_assoc();
    else if (test == "test_unary_minus")        test_unary_minus();
    else if (test == "test_parens")             test_parens();
    else if (test == "test_complex")            test_complex();
    else if (test == "test_nested_parens")      test_nested_parens();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
