#include "bplus_tree.hpp"
#include <iostream>
#include <string>

void test_insert_search() {
    BPlusTree tree;
    for (int i = 1; i <= 10; ++i) tree.insert(i);
    bool ok = true;
    for (int i = 1; i <= 10; ++i) if (!tree.search(i)) ok = false;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_search" << std::endl;
}

void test_remove_keeps_others() {
    BPlusTree tree;
    for (int i = 1; i <= 20; ++i) tree.insert(i);
    tree.remove(5);
    tree.remove(10);
    tree.remove(15);
    bool ok = !tree.search(5) && !tree.search(10) && !tree.search(15);
    ok = ok && tree.search(1) && tree.search(7) && tree.search(20);
    ok = ok && (tree.size() == 17);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_remove_keeps_others" << std::endl;
}

void test_redistribute_updates_parent() {
    BPlusTree tree;
    for (int i = 1; i <= 12; ++i) tree.insert(i);
    // Remove enough to trigger redistribution
    tree.remove(1);
    tree.remove(2);
    bool ok = tree.search(3) && tree.search(12);
    auto all = tree.all_keys();
    ok = ok && ((int)all.size() == 10);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_redistribute_updates_parent" << std::endl;
}

void test_range_after_delete() {
    BPlusTree tree;
    for (int i = 1; i <= 30; ++i) tree.insert(i);
    for (int i = 1; i <= 10; ++i) tree.remove(i);
    auto range = tree.range_query(11, 20);
    bool ok = ((int)range.size() == 10);
    for (int i = 0; i < 10 && ok; ++i) {
        if (range[i] != i + 11) ok = false;
    }
    std::cout << (ok ? "PASS" : "FAIL") << ": test_range_after_delete" << std::endl;
}

void test_all_keys_sorted() {
    BPlusTree tree;
    tree.insert(5); tree.insert(3); tree.insert(8); tree.insert(1);
    auto keys = tree.all_keys();
    bool ok = (keys.size() == 4) && (keys[0]==1) && (keys[1]==3) && (keys[2]==5) && (keys[3]==8);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_all_keys_sorted" << std::endl;
}

void test_range_query_basic() {
    BPlusTree tree;
    for (int i = 1; i <= 10; ++i) tree.insert(i);
    auto range = tree.range_query(3, 7);
    bool ok = (range.size() == 5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_range_query_basic" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_insert_search")               test_insert_search();
    else if (test == "test_remove_keeps_others")         test_remove_keeps_others();
    else if (test == "test_redistribute_updates_parent") test_redistribute_updates_parent();
    else if (test == "test_range_after_delete")          test_range_after_delete();
    else if (test == "test_all_keys_sorted")             test_all_keys_sorted();
    else if (test == "test_range_query_basic")           test_range_query_basic();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
