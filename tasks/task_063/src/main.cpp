#include "pool_allocator.hpp"
#include <iostream>
#include <string>

void test_basic_alloc_dealloc() {
    PoolAllocator pool(1024);
    auto a = pool.allocate(100);
    auto b = pool.allocate(200);
    pool.deallocate(a);
    pool.deallocate(b);
    bool ok = (pool.available() == 1024);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_basic_alloc_dealloc" << std::endl;
}

void test_coalesce_adjacent() {
    PoolAllocator pool(1024);
    auto a = pool.allocate(256);
    auto b = pool.allocate(256);
    auto c = pool.allocate(256);
    pool.deallocate(a);
    pool.deallocate(b);
    // After coalescing a and b, should have one 512-byte free block
    bool ok = (pool.largest_free() == 512);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_coalesce_adjacent" << std::endl;
}

void test_coalesce_all_free() {
    PoolAllocator pool(1024);
    auto a = pool.allocate(100);
    auto b = pool.allocate(200);
    auto c = pool.allocate(300);
    pool.deallocate(b);
    pool.deallocate(a);
    pool.deallocate(c);
    // All freed and coalesced — should be one block of 1024
    bool ok = (pool.largest_free() == 1024) && (pool.num_blocks() == 1);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_coalesce_all_free" << std::endl;
}

void test_alloc_after_coalesce() {
    PoolAllocator pool(512);
    auto a = pool.allocate(128);
    auto b = pool.allocate(128);
    auto c = pool.allocate(128);
    pool.deallocate(a);
    pool.deallocate(b);
    // Coalesced 256 free, can allocate 256
    auto d = pool.allocate(256);
    bool ok = (d == 0);  // should reuse start
    std::cout << (ok ? "PASS" : "FAIL") << ": test_alloc_after_coalesce" << std::endl;
}

void test_simple_alloc() {
    PoolAllocator pool(256);
    auto a = pool.allocate(64);
    auto b = pool.allocate(64);
    bool ok = (a == 0) && (b == 64) && (pool.available() == 128);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_simple_alloc" << std::endl;
}

void test_available() {
    PoolAllocator pool(100);
    pool.allocate(30);
    pool.allocate(20);
    bool ok = (pool.available() == 50);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_available" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_basic_alloc_dealloc")  test_basic_alloc_dealloc();
    else if (test == "test_coalesce_adjacent")    test_coalesce_adjacent();
    else if (test == "test_coalesce_all_free")    test_coalesce_all_free();
    else if (test == "test_alloc_after_coalesce") test_alloc_after_coalesce();
    else if (test == "test_simple_alloc")         test_simple_alloc();
    else if (test == "test_available")            test_available();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
