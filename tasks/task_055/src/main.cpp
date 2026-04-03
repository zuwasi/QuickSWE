#include <iostream>
#include <string>
#include <cstring>
#include <algorithm>
#include "bst.hpp"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <test_name>" << std::endl;
        return 1;
    }

    std::string test = argv[1];

    if (test == "basic_insert_find") {
        BST<int> tree;
        tree.insert(50);
        tree.insert(30);
        tree.insert(70);
        tree.insert(20);
        tree.insert(40);

        bool ok = true;
        int vals[] = {20, 30, 40, 50, 70};
        for (int v : vals) {
            if (!tree.find(v)) {
                std::cout << "FAIL: could not find " << v << std::endl;
                ok = false;
            }
        }
        if (tree.find(99)) {
            std::cout << "FAIL: found 99 which was not inserted" << std::endl;
            ok = false;
        }

        std::string order = tree.inorder_string();
        if (order != "20 30 40 50 70") {
            std::cout << "FAIL: inorder = [" << order << "]" << std::endl;
            ok = false;
        }

        if (ok) std::cout << "PASS: basic_insert_find" << std::endl;

    } else if (test == "delete_leaf") {
        BST<int> tree;
        tree.insert(50);
        tree.insert(30);
        tree.insert(70);

        tree.remove(30);  /* leaf node */
        if (tree.find(30)) {
            std::cout << "FAIL: 30 still found after delete" << std::endl;
        } else {
            std::string order = tree.inorder_string();
            if (order == "50 70") {
                std::cout << "PASS: delete_leaf" << std::endl;
            } else {
                std::cout << "FAIL: inorder = [" << order << "]" << std::endl;
            }
        }

    } else if (test == "delete_two_children") {
        /*
         * This test exposes the bug:
         * Tree:       50
         *           /    \
         *         30      70
         *        / \     / \
         *      20  40  60  80
         *          /      /  \
         *        35     75   85
         *                \
         *                77
         *
         * Delete 70: in-order successor is 75 (min of right subtree).
         * 75 has a right child (77). After replacing 70 with 75,
         * 77 must be relinked as the left child of 80.
         * BUG: the manual unlinking sets parent->left = nullptr,
         * dropping 77 entirely.
         */
        BST<int> tree;
        int inserts[] = {50, 30, 70, 20, 40, 60, 80, 35, 75, 85, 77};
        for (int v : inserts) {
            tree.insert(v);
        }

        std::cout << "BEFORE: " << tree.inorder_string() << std::endl;
        std::cout << "VALID_BST_BEFORE: " << (tree.is_valid_bst() ? "yes" : "no") << std::endl;

        tree.remove(70);

        std::string after = tree.inorder_string();
        std::cout << "AFTER: " << after << std::endl;
        std::cout << "VALID_BST_AFTER: " << (tree.is_valid_bst() ? "yes" : "no") << std::endl;

        /* Check all remaining elements are findable */
        int expected[] = {20, 30, 35, 40, 50, 60, 75, 77, 80, 85};
        bool all_found = true;
        for (int v : expected) {
            if (!tree.find(v)) {
                std::cout << "MISSING: " << v << std::endl;
                all_found = false;
            }
        }

        if (all_found && tree.is_valid_bst() && after == "20 30 35 40 50 60 75 77 80 85") {
            std::cout << "RESULT: CORRECT" << std::endl;
        } else {
            std::cout << "RESULT: CORRUPTED" << std::endl;
        }

    } else if (test == "delete_successor_is_right_child") {
        /*
         * Case where successor IS the immediate right child.
         * Tree:    10
         *            \
         *            20
         *              \
         *              30
         *
         * Delete 10: successor is 20 (immediate right child).
         * 20 replaces 10, must keep 30.
         */
        BST<int> tree;
        tree.insert(10);
        tree.insert(5);
        tree.insert(20);
        tree.insert(30);

        tree.remove(10);

        std::string after = tree.inorder_string();
        std::cout << "AFTER: " << after << std::endl;

        bool ok = tree.find(5) && tree.find(20) && tree.find(30) && !tree.find(10);
        ok = ok && tree.is_valid_bst();
        ok = ok && (after == "5 20 30");

        if (ok) {
            std::cout << "RESULT: CORRECT" << std::endl;
        } else {
            std::cout << "RESULT: CORRUPTED" << std::endl;
            std::cout << "VALID: " << (tree.is_valid_bst() ? "yes" : "no") << std::endl;
        }

    } else if (test == "multiple_deletes") {
        /*
         * Multiple deletions that exercise the bug repeatedly.
         * Each deleted node's in-order successor has a right child,
         * which must be properly relinked.
         *
         * Tree structure:
         *              50
         *           /      \
         *         25        75
         *        / \       / \
         *      10   30   60   90
         *      /\   /\   /\   /\
         *     5 15 27 35 55 65 80 95
         *        \   \    \     \
         *        17  29   67    82
         *
         * Delete 25: successor=27, 27 has right child 29 -> 29 must survive
         * Delete 75: successor=80, 80 has right child 82 -> 82 must survive
         * Delete 50: successor=55 (after restructure), 55 has right child 67 -> 67 must survive
         */
        BST<int> tree;
        for (int v : {50, 25, 75, 10, 30, 60, 90, 5, 15, 27, 35, 55, 65, 80, 95, 17, 29, 67, 82}) {
            tree.insert(v);
        }

        std::cout << "INITIAL: " << tree.inorder_string() << std::endl;

        /* Delete 25: successor is 27, which has right child 29 */
        tree.remove(25);
        std::cout << "AFTER_DEL_25: " << tree.inorder_string() << std::endl;

        /* Delete 75: successor is 80, which has right child 82 */
        tree.remove(75);
        std::cout << "AFTER_DEL_75: " << tree.inorder_string() << std::endl;

        /* Delete 50: successor depends on tree shape after above deletes */
        tree.remove(50);
        std::cout << "AFTER_DEL_50: " << tree.inorder_string() << std::endl;

        /* All of these must survive: 5,10,15,17,27,29,30,35,55,60,65,67,80,82,90,95 */
        /* Minus the deleted ones (25,75,50) and the successors that replaced them stay */
        int remaining[] = {5, 10, 15, 17, 29, 30, 35, 55, 60, 65, 67, 80, 82, 90, 95};
        bool all_found = true;
        for (int v : remaining) {
            if (!tree.find(v)) {
                std::cout << "MISSING: " << v << std::endl;
                all_found = false;
            }
        }

        /* Verify BST property */
        std::vector<int> order = tree.inorder();
        bool sorted = std::is_sorted(order.begin(), order.end());

        if (all_found && sorted && tree.is_valid_bst()) {
            std::cout << "RESULT: CORRECT" << std::endl;
        } else {
            std::cout << "RESULT: CORRUPTED" << std::endl;
        }

    } else {
        std::cout << "Unknown test: " << test << std::endl;
        return 1;
    }

    return 0;
}
