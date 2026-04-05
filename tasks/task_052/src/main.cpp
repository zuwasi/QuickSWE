#include "tokenizer.hpp"
#include <iostream>
#include <string>

void test_basic_split() {
    auto tokens = Tokenizer::split("a,b,c", ',');
    bool ok = tokens.size() == 3 && tokens[0] == "a" && tokens[1] == "b" && tokens[2] == "c";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_split" << std::endl;
}

void test_escaped_delimiter() {
    auto tokens = Tokenizer::split("a\\,b,c", ',');
    bool ok = tokens.size() == 2 && tokens[0] == "a,b" && tokens[1] == "c";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_escaped_delimiter" << std::endl;
}

void test_escaped_backslash_before_delim() {
    // "a\\\\,b" => input chars: a \ \ , b
    // \\  is escaped backslash -> literal backslash
    // then , is real delimiter
    auto tokens = Tokenizer::split("a\\\\,b", ',');
    bool ok = tokens.size() == 2 && tokens[0] == "a\\" && tokens[1] == "b";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_escaped_backslash_before_delim" << std::endl;
}

void test_trailing_escape() {
    auto tokens = Tokenizer::split("a\\", ',');
    bool ok = tokens.size() == 1 && tokens[0] == "a\\";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_trailing_escape" << std::endl;
}

void test_empty_tokens() {
    auto tokens = Tokenizer::split(",a,,b,", ',');
    bool ok = tokens.size() == 5 && tokens[0].empty() && tokens[2].empty() && tokens[4].empty();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_empty_tokens" << std::endl;
}

void test_no_delimiter() {
    auto tokens = Tokenizer::split("hello", ',');
    bool ok = tokens.size() == 1 && tokens[0] == "hello";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_no_delimiter" << std::endl;
}

void test_roundtrip() {
    std::vector<std::string> original = {"a,b", "c\\d", "e"};
    std::string escaped;
    for (size_t i = 0; i < original.size(); ++i) {
        if (i > 0) escaped += ',';
        escaped += Tokenizer::escape(original[i], ',');
    }
    auto restored = Tokenizer::split(escaped, ',');
    bool ok = restored == original;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_roundtrip" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <test_name>" << std::endl;
        return 1;
    }
    std::string test(argv[1]);
    if      (test == "test_basic_split")                   test_basic_split();
    else if (test == "test_escaped_delimiter")             test_escaped_delimiter();
    else if (test == "test_escaped_backslash_before_delim") test_escaped_backslash_before_delim();
    else if (test == "test_trailing_escape")               test_trailing_escape();
    else if (test == "test_empty_tokens")                  test_empty_tokens();
    else if (test == "test_no_delimiter")                  test_no_delimiter();
    else if (test == "test_roundtrip")                     test_roundtrip();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
