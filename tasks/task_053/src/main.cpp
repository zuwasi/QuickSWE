#include "matrix.hpp"
#include <iostream>
#include <string>

void test_square_multiply() {
    Matrix a(2, 2), b(2, 2);
    a.at(0,0)=1; a.at(0,1)=2; a.at(1,0)=3; a.at(1,1)=4;
    b.at(0,0)=5; b.at(0,1)=6; b.at(1,0)=7; b.at(1,1)=8;
    auto c = a.multiply(b);
    // Expected: [[19,22],[43,50]]
    bool ok = (c.at(0,0)==19) && (c.at(0,1)==22) && (c.at(1,0)==43) && (c.at(1,1)==50);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_square_multiply" << std::endl;
}

void test_rect_multiply() {
    Matrix a(2, 3), b(3, 2);
    a.at(0,0)=1; a.at(0,1)=2; a.at(0,2)=3;
    a.at(1,0)=4; a.at(1,1)=5; a.at(1,2)=6;
    b.at(0,0)=7; b.at(0,1)=8;
    b.at(1,0)=9; b.at(1,1)=10;
    b.at(2,0)=11; b.at(2,1)=12;
    auto c = a.multiply(b);
    // Expected: [[58,64],[139,154]]
    bool ok = (c.rows()==2) && (c.cols()==2) &&
              (c.at(0,0)==58) && (c.at(0,1)==64) &&
              (c.at(1,0)==139) && (c.at(1,1)==154);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_rect_multiply" << std::endl;
}

void test_identity_property() {
    Matrix a(2, 3);
    a.at(0,0)=1; a.at(0,1)=2; a.at(0,2)=3;
    a.at(1,0)=4; a.at(1,1)=5; a.at(1,2)=6;
    auto I = Matrix::identity(3);
    auto c = a.multiply(I);
    bool ok = c.equals(a);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_identity_property" << std::endl;
}

void test_transpose_product() {
    Matrix a(2, 3), b(3, 2);
    a.at(0,0)=1; a.at(0,1)=2; a.at(0,2)=3;
    a.at(1,0)=4; a.at(1,1)=5; a.at(1,2)=6;
    b.at(0,0)=7; b.at(0,1)=8;
    b.at(1,0)=9; b.at(1,1)=10;
    b.at(2,0)=11; b.at(2,1)=12;
    auto ab_t = a.multiply(b).transpose();
    auto bt_at = b.transpose().multiply(a.transpose());
    bool ok = ab_t.equals(bt_at);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_transpose_product" << std::endl;
}

void test_result_dimensions() {
    Matrix a(3, 4), b(4, 2);
    auto c = a.multiply(b);
    bool ok = (c.rows() == 3) && (c.cols() == 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_result_dimensions" << std::endl;
}

void test_transpose_basic() {
    Matrix a(2, 3);
    a.at(0,0)=1; a.at(0,1)=2; a.at(0,2)=3;
    a.at(1,0)=4; a.at(1,1)=5; a.at(1,2)=6;
    auto t = a.transpose();
    bool ok = (t.rows()==3) && (t.cols()==2) &&
              (t.at(0,0)==1) && (t.at(1,0)==2) && (t.at(2,0)==3);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_transpose_basic" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_square_multiply")   test_square_multiply();
    else if (test == "test_rect_multiply")     test_rect_multiply();
    else if (test == "test_identity_property") test_identity_property();
    else if (test == "test_transpose_product") test_transpose_product();
    else if (test == "test_result_dimensions") test_result_dimensions();
    else if (test == "test_transpose_basic")   test_transpose_basic();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
