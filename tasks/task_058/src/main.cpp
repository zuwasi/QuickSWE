#include "lockfree_stack.hpp"
#include <iostream>
#include <string>

void test_basic_lifo() {
    LockFreeStack<int> s;
    s.push(1); s.push(2); s.push(3);
    auto a = s.pop().value();
    auto b = s.pop().value();
    auto c = s.pop().value();
    bool ok = (a == 3) && (b == 2) && (c == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_lifo" << std::endl;
}

void test_push_pop_push_sequence() {
    LockFreeStack<int> s;
    s.push(10);
    s.push(20);
    auto v1 = s.pop().value();  // 20
    s.push(30);
    auto v2 = s.pop().value();  // 30
    auto v3 = s.pop().value();  // 10
    bool ok = (v1 == 20) && (v2 == 30) && (v3 == 10);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_push_pop_push_sequence" << std::endl;
}

void test_tag_increments_on_push() {
    LockFreeStack<int> s;
    s.push(1);
    s.push(2);
    s.pop();
    s.push(3);
    // After push-push-pop-push, stack should be [1, 3] (bottom to top)
    auto top = s.pop().value();
    auto bot = s.pop().value();
    bool ok = (top == 3) && (bot == 1) && s.empty();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_tag_increments_on_push" << std::endl;
}

void test_drain() {
    LockFreeStack<int> s;
    for (int i = 0; i < 5; ++i) s.push(i);
    auto items = s.drain();
    bool ok = (items.size() == 5) && (items[0] == 4) && (items[4] == 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_drain" << std::endl;
}

void test_empty_pop() {
    LockFreeStack<int> s;
    auto v = s.pop();
    bool ok = !v.has_value();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_empty_pop" << std::endl;
}

void test_size() {
    LockFreeStack<int> s;
    s.push(1); s.push(2); s.push(3);
    s.pop();
    bool ok = (s.size() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_size" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_basic_lifo")              test_basic_lifo();
    else if (test == "test_push_pop_push_sequence")  test_push_pop_push_sequence();
    else if (test == "test_tag_increments_on_push")  test_tag_increments_on_push();
    else if (test == "test_drain")                   test_drain();
    else if (test == "test_empty_pop")               test_empty_pop();
    else if (test == "test_size")                    test_size();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
