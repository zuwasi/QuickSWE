#include "circular_buffer.hpp"
#include <iostream>
#include <string>
#include <cstring>

void test_basic_push_pop() {
    CircularBuffer<int, 4> cb;
    cb.push_back(1);
    cb.push_back(2);
    cb.push_back(3);
    bool ok = (cb.pop_front() == 1) && (cb.pop_front() == 2) && (cb.pop_front() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_push_pop" << std::endl;
}

void test_size_after_wrap() {
    CircularBuffer<int, 3> cb;
    cb.push_back(10);
    cb.push_back(20);
    cb.push_back(30);
    cb.push_back(40);  // overwrite 10
    bool ok = (cb.size() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_size_after_wrap" << std::endl;
}

void test_overwrite_oldest() {
    CircularBuffer<int, 3> cb;
    for (int i = 1; i <= 5; ++i) cb.push_back(i);
    // Should contain 3, 4, 5
    bool ok = (cb.front() == 3) && (cb.back() == 5) && (cb.size() == 3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_overwrite_oldest" << std::endl;
}

void test_to_vector_wrapped() {
    CircularBuffer<int, 4> cb;
    for (int i = 1; i <= 6; ++i) cb.push_back(i);
    auto v = cb.to_vector();
    bool ok = (v.size() == 4) && (v[0] == 3) && (v[1] == 4) && (v[2] == 5) && (v[3] == 6);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_to_vector_wrapped" << std::endl;
}

void test_empty_after_drain() {
    CircularBuffer<int, 2> cb;
    cb.push_back(1);
    cb.push_back(2);
    cb.pop_front();
    cb.pop_front();
    bool ok = cb.empty() && (cb.size() == 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_empty_after_drain" << std::endl;
}

void test_single_element() {
    CircularBuffer<int, 1> cb;
    cb.push_back(42);
    bool ok = (cb.size() == 1) && (cb.front() == 42) && (cb.back() == 42);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_single_element" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <test_name>" << std::endl;
        return 1;
    }
    std::string test(argv[1]);
    if (test == "test_basic_push_pop")    test_basic_push_pop();
    else if (test == "test_size_after_wrap")   test_size_after_wrap();
    else if (test == "test_overwrite_oldest")  test_overwrite_oldest();
    else if (test == "test_to_vector_wrapped") test_to_vector_wrapped();
    else if (test == "test_empty_after_drain") test_empty_after_drain();
    else if (test == "test_single_element")    test_single_element();
    else {
        std::cerr << "Unknown test: " << test << std::endl;
        return 1;
    }
    return 0;
}
