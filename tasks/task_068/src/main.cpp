#include "regex_engine.hpp"
#include <iostream>
#include <string>

void test_literal() {
    RegexEngine re;
    re.compile("abc");
    bool ok = re.match("abc") && !re.match("ab") && !re.match("abcd");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_literal" << std::endl;
}

void test_alternation() {
    RegexEngine re;
    re.compile("a|b");
    bool ok = re.match("a") && re.match("b") && !re.match("c") && !re.match("ab");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_alternation" << std::endl;
}

void test_star() {
    RegexEngine re;
    re.compile("a*");
    bool ok = re.match("") && re.match("a") && re.match("aaa") && !re.match("b");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_star" << std::endl;
}

void test_plus() {
    RegexEngine re;
    re.compile("a+");
    bool ok = !re.match("") && re.match("a") && re.match("aaa") && !re.match("b");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_plus" << std::endl;
}

void test_question() {
    RegexEngine re;
    re.compile("a?");
    bool ok = re.match("") && re.match("a") && !re.match("aa");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_question" << std::endl;
}

void test_concat_star() {
    RegexEngine re;
    re.compile("ab*c");
    bool ok = re.match("ac") && re.match("abc") && re.match("abbc") && !re.match("abbd");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_concat_star" << std::endl;
}

void test_complex_pattern() {
    RegexEngine re;
    re.compile("(a|b)*c");
    bool ok = re.match("c") && re.match("ac") && re.match("bc") && re.match("ababc") && !re.match("abc ");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_complex_pattern" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_literal")          test_literal();
    else if (test == "test_alternation")      test_alternation();
    else if (test == "test_star")             test_star();
    else if (test == "test_plus")             test_plus();
    else if (test == "test_question")         test_question();
    else if (test == "test_concat_star")      test_concat_star();
    else if (test == "test_complex_pattern")  test_complex_pattern();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
