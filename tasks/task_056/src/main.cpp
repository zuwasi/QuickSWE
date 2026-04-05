#include "sfinae_dispatch.hpp"
#include <iostream>
#include <string>

struct Serializable {
    int data;
    std::string serialize() const { return "data=" + std::to_string(data); }
};

struct Plain {
    int x;
};

void test_arithmetic_value() {
    auto r = serialize(42);
    bool ok = r.find("arithmetic:") == 0;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_arithmetic_value" << std::endl;
}

void test_arithmetic_const_ref() {
    const int& val = *new int(42);
    auto cls = classify<decltype(val)>();
    bool ok = (cls == "arithmetic");
    delete &val;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_arithmetic_const_ref" << std::endl;
}

void test_custom_value() {
    Serializable s{10};
    auto r = serialize(s);
    bool ok = (r == "custom:data=10");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_custom_value" << std::endl;
}

void test_custom_const_ref() {
    const Serializable& s = Serializable{20};
    auto cls = classify<decltype(s)>();
    bool ok = (cls == "custom");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_custom_const_ref" << std::endl;
}

void test_fallback() {
    Plain p{5};
    auto r = serialize(p);
    bool ok = (r == "fallback:unknown");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_fallback" << std::endl;
}

void test_fallback_const_ref() {
    const Plain& p = Plain{5};
    auto cls = classify<decltype(p)>();
    bool ok = (cls == "fallback");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_fallback_const_ref" << std::endl;
}

void test_double_const_ref() {
    const double& val = 3.14;
    auto cls = classify<decltype(val)>();
    bool ok = (cls == "arithmetic");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_double_const_ref" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_arithmetic_value")     test_arithmetic_value();
    else if (test == "test_arithmetic_const_ref") test_arithmetic_const_ref();
    else if (test == "test_custom_value")         test_custom_value();
    else if (test == "test_custom_const_ref")     test_custom_const_ref();
    else if (test == "test_fallback")             test_fallback();
    else if (test == "test_fallback_const_ref")   test_fallback_const_ref();
    else if (test == "test_double_const_ref")     test_double_const_ref();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
