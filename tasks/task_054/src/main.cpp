#include "min_heap.hpp"
#include <iostream>
#include <string>

void test_basic_push_pop() {
    MinHeap<int> h;
    h.push(3); h.push(1); h.push(2);
    bool ok = (h.pop() == 1) && (h.pop() == 2) && (h.pop() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_push_pop" << std::endl;
}

void test_descending_insert() {
    MinHeap<int> h;
    for (int i = 10; i >= 1; --i) h.push(i);
    auto sorted = h.sorted_extract();
    bool ok = true;
    for (int i = 0; i < 10; ++i) {
        if (sorted[i] != i + 1) { ok = false; break; }
    }
    std::cout << (ok ? "PASS" : "FAIL") << ": test_descending_insert" << std::endl;
}

void test_duplicates() {
    MinHeap<int> h;
    h.push(5); h.push(3); h.push(5); h.push(3); h.push(1);
    auto sorted = h.sorted_extract();
    bool ok = (sorted.size() == 5) && (sorted[0] == 1) && (sorted[1] == 3) &&
              (sorted[2] == 3) && (sorted[3] == 5) && (sorted[4] == 5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_duplicates" << std::endl;
}

void test_single_element() {
    MinHeap<int> h;
    h.push(42);
    bool ok = (h.top() == 42) && (h.pop() == 42) && h.empty();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_single_element" << std::endl;
}

void test_large_heap() {
    MinHeap<int> h;
    for (int i = 100; i >= 1; --i) h.push(i);
    auto sorted = h.sorted_extract();
    bool ok = true;
    for (int i = 1; i < 100; ++i) {
        if (sorted[i] < sorted[i-1]) { ok = false; break; }
    }
    std::cout << (ok ? "PASS" : "FAIL") << ": test_large_heap" << std::endl;
}

void test_interleaved() {
    MinHeap<int> h;
    h.push(5); h.push(3);
    int v1 = h.pop(); // should be 3
    h.push(1); h.push(4);
    int v2 = h.pop(); // should be 1
    bool ok = (v1 == 3) && (v2 == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_interleaved" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_basic_push_pop")     test_basic_push_pop();
    else if (test == "test_descending_insert")  test_descending_insert();
    else if (test == "test_duplicates")         test_duplicates();
    else if (test == "test_single_element")     test_single_element();
    else if (test == "test_large_heap")         test_large_heap();
    else if (test == "test_interleaved")        test_interleaved();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
