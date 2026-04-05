#include "btree_lazy.hpp"
#include <iostream>
#include <string>

void test_insert_search() {
    BTreeLazy tree;
    for (int i = 1; i <= 10; ++i) tree.insert(i);
    bool ok = true;
    for (int i = 1; i <= 10; ++i) if (!tree.search(i)) ok = false;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_insert_search" << std::endl;
}

void test_lazy_remove() {
    BTreeLazy tree;
    for (int i = 1; i <= 5; ++i) tree.insert(i);
    tree.lazy_remove(3);
    bool ok = !tree.search(3) && tree.search(2) && tree.search(4);
    ok = ok && (tree.active_count() == 4);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_lazy_remove" << std::endl;
}

void test_compact_preserves_keys() {
    BTreeLazy tree;
    for (int i = 1; i <= 10; ++i) tree.insert(i);
    tree.lazy_remove(3);
    tree.lazy_remove(7);
    tree.compact();
    bool ok = (tree.active_count() == 8);
    ok = ok && !tree.search(3) && !tree.search(7);
    ok = ok && tree.search(1) && tree.search(5) && tree.search(10);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_compact_preserves_keys" << std::endl;
}

void test_inorder_after_compact() {
    BTreeLazy tree;
    for (int i = 10; i >= 1; --i) tree.insert(i);
    tree.lazy_remove(5);
    tree.compact();
    auto keys = tree.inorder();
    bool ok = true;
    for (int i = 1; i < (int)keys.size(); ++i)
        if (keys[i] <= keys[i-1]) ok = false;
    ok = ok && ((int)keys.size() == 9);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_inorder_after_compact" << std::endl;
}

void test_heavy_delete_compact() {
    BTreeLazy tree;
    for (int i = 1; i <= 20; ++i) tree.insert(i);
    for (int i = 1; i <= 15; ++i) tree.lazy_remove(i);
    tree.compact();
    bool ok = (tree.active_count() == 5);
    for (int i = 16; i <= 20; ++i) {
        if (!tree.search(i)) ok = false;
    }
    std::cout << (ok ? "PASS" : "FAIL") << ": test_heavy_delete_compact" << std::endl;
}

void test_inorder_basic() {
    BTreeLazy tree;
    tree.insert(5); tree.insert(3); tree.insert(8); tree.insert(1);
    auto keys = tree.inorder();
    bool ok = (keys.size() == 4) && (keys[0]==1) && (keys[1]==3) && (keys[2]==5) && (keys[3]==8);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_inorder_basic" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_insert_search")         test_insert_search();
    else if (test == "test_lazy_remove")           test_lazy_remove();
    else if (test == "test_compact_preserves_keys") test_compact_preserves_keys();
    else if (test == "test_inorder_after_compact") test_inorder_after_compact();
    else if (test == "test_heavy_delete_compact")  test_heavy_delete_compact();
    else if (test == "test_inorder_basic")         test_inorder_basic();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
