#include "patricia_trie.hpp"
#include <iostream>
#include <string>

void test_insert_search_basic() {
    PatriciaTrie trie;
    trie.insert("hello");
    trie.insert("world");
    bool ok = trie.search("hello") && trie.search("world") && !trie.search("hell");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_search_basic" << std::endl;
}

void test_prefix_then_full() {
    PatriciaTrie trie;
    trie.insert("testing");
    trie.insert("test");
    bool ok = trie.search("test") && trie.search("testing");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_prefix_then_full" << std::endl;
}

void test_split_diverge() {
    PatriciaTrie trie;
    trie.insert("abc");
    trie.insert("abd");
    bool ok = trie.search("abc") && trie.search("abd") && !trie.search("ab");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_split_diverge" << std::endl;
}

void test_all_keys() {
    PatriciaTrie trie;
    trie.insert("car"); trie.insert("card"); trie.insert("care"); trie.insert("cat");
    auto keys = trie.all_keys();
    bool ok = (keys.size() == 4) && keys[0]=="car" && keys[1]=="card" && keys[2]=="care" && keys[3]=="cat";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_all_keys" << std::endl;
}

void test_starts_with() {
    PatriciaTrie trie;
    trie.insert("apple"); trie.insert("app"); trie.insert("banana");
    bool ok = trie.starts_with("app") && trie.starts_with("ban") && !trie.starts_with("cat");
    std::cout << (ok ? "PASS" : "FAIL") << ": test_starts_with" << std::endl;
}

void test_size() {
    PatriciaTrie trie;
    trie.insert("a"); trie.insert("ab"); trie.insert("abc");
    bool ok = (trie.size() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_size" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_insert_search_basic") test_insert_search_basic();
    else if (test == "test_prefix_then_full")    test_prefix_then_full();
    else if (test == "test_split_diverge")       test_split_diverge();
    else if (test == "test_all_keys")            test_all_keys();
    else if (test == "test_starts_with")         test_starts_with();
    else if (test == "test_size")                test_size();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
