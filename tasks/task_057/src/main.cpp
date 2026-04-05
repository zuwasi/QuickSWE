#include "shared_ptr.hpp"
#include <iostream>
#include <string>

static int alive_count = 0;

struct Tracked {
    int value;
    Tracked(int v) : value(v) { ++alive_count; }
    ~Tracked() { --alive_count; }
};

void test_basic_usage() {
    alive_count = 0;
    {
        SharedPtr<Tracked> p(new Tracked(1));
        bool ok = (p.use_count() == 1) && (p->value == 1);
        std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_usage" << std::endl;
    }
    // Tracked should be destroyed
    if (alive_count != 0) {
        std::cout << "FAIL: test_basic_usage (leak)" << std::endl;
    }
}

void test_copy_construct() {
    SharedPtr<Tracked> a(new Tracked(2));
    SharedPtr<Tracked> b(a);
    bool ok = (a.use_count() == 2) && (b.use_count() == 2) && (a.get() == b.get());
    std::cout << (ok ? "PASS" : "FAIL") << ": test_copy_construct" << std::endl;
}

void test_self_assignment() {
    alive_count = 0;
    {
        SharedPtr<Tracked> a(new Tracked(3));
        a = a;
        bool ok = (a.use_count() == 1) && (a->value == 3) && (alive_count == 1);
        std::cout << (ok ? "PASS" : "FAIL") << ": test_self_assignment" << std::endl;
    }
}

void test_copy_assign_releases_old() {
    alive_count = 0;
    {
        SharedPtr<Tracked> a(new Tracked(10));
        SharedPtr<Tracked> b(new Tracked(20));
        b = a;  // old Tracked(20) should be freed
        bool ok = (alive_count == 1) && (b->value == 10) && (a.use_count() == 2);
        std::cout << (ok ? "PASS" : "FAIL") << ": test_copy_assign_releases_old" << std::endl;
    }
}

void test_chain_assignment() {
    alive_count = 0;
    {
        SharedPtr<Tracked> a(new Tracked(1));
        SharedPtr<Tracked> b(new Tracked(2));
        SharedPtr<Tracked> c(new Tracked(3));
        c = b;
        b = a;
        bool ok = (alive_count == 2) && (a.use_count() == 2) && (c.use_count() == 1);
        std::cout << (ok ? "PASS" : "FAIL") << ": test_chain_assignment" << std::endl;
    }
    bool ok = (alive_count == 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_chain_no_leak" << std::endl;
}

void test_move() {
    SharedPtr<Tracked> a(new Tracked(5));
    SharedPtr<Tracked> b(std::move(a));
    bool ok = (!a) && (b.use_count() == 1) && (b->value == 5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_move" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_basic_usage")              test_basic_usage();
    else if (test == "test_copy_construct")           test_copy_construct();
    else if (test == "test_self_assignment")           test_self_assignment();
    else if (test == "test_copy_assign_releases_old") test_copy_assign_releases_old();
    else if (test == "test_chain_assignment")          test_chain_assignment();
    else if (test == "test_move")                      test_move();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
