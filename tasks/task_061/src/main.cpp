#include "rbtree.hpp"
#include <iostream>
#include <string>
#include <cmath>

void test_sorted_insert_valid() {
    RBTree<int> tree;
    for (int i = 1; i <= 15; ++i) tree.insert(i);
    bool ok = tree.validate();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_sorted_insert_valid" << std::endl;
}

void test_reverse_insert_valid() {
    RBTree<int> tree;
    for (int i = 15; i >= 1; --i) tree.insert(i);
    bool ok = tree.validate();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_reverse_insert_valid" << std::endl;
}

void test_height_logarithmic() {
    RBTree<int> tree;
    for (int i = 1; i <= 100; ++i) tree.insert(i);
    int h = tree.height();
    // RB tree height <= 2*log2(n+1)
    int max_h = (int)(2.0 * std::log2(101.0)) + 1;
    bool ok = (h <= max_h);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_height_logarithmic" << std::endl;
}

void test_inorder_sorted() {
    RBTree<int> tree;
    tree.insert(5); tree.insert(3); tree.insert(8);
    tree.insert(1); tree.insert(4); tree.insert(7);
    auto v = tree.inorder();
    bool ok = (v.size() == 6);
    for (std::size_t i = 1; i < v.size() && ok; ++i)
        if (v[i] <= v[i-1]) ok = false;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_inorder_sorted" << std::endl;
}

void test_search() {
    RBTree<int> tree;
    for (int i = 1; i <= 10; ++i) tree.insert(i);
    bool ok = tree.search(5) && tree.search(1) && tree.search(10) && !tree.search(11);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_search" << std::endl;
}

void test_zigzag_valid() {
    RBTree<int> tree;
    int vals[] = {10, 5, 15, 3, 7, 12, 20, 1, 4, 6, 8};
    for (int v : vals) tree.insert(v);
    bool ok = tree.validate();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_zigzag_valid" << std::endl;
}

void test_large_valid() {
    RBTree<int> tree;
    for (int i = 1; i <= 500; ++i) tree.insert(i);
    bool ok = tree.validate() && (tree.size() == 500);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_large_valid" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_sorted_insert_valid")  test_sorted_insert_valid();
    else if (test == "test_reverse_insert_valid") test_reverse_insert_valid();
    else if (test == "test_height_logarithmic")   test_height_logarithmic();
    else if (test == "test_inorder_sorted")       test_inorder_sorted();
    else if (test == "test_search")               test_search();
    else if (test == "test_zigzag_valid")         test_zigzag_valid();
    else if (test == "test_large_valid")          test_large_valid();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
