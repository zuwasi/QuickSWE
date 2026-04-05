#include "simd_matrix.hpp"
#include <iostream>
#include <string>
#include <cmath>

bool close(double a, double b, double eps = 1e-6) { return std::abs(a - b) < eps; }

void test_identity_multiply() {
    auto I = Mat4::identity();
    auto A = Mat4::from_rows({1,2,3,4, 5,6,7,8, 9,10,11,12, 13,14,15,16});
    auto R = A.multiply(I);
    bool ok = R.close_to(A);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_identity_multiply" << std::endl;
}

void test_multiply_known() {
    auto A = Mat4::from_rows({1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1});
    auto B = Mat4::from_rows({2,0,0,0, 0,3,0,0, 0,0,4,0, 0,0,0,5});
    auto R = A.multiply(B);
    bool ok = close(R.at(0,0), 2) && close(R.at(1,1), 3) &&
              close(R.at(2,2), 4) && close(R.at(3,3), 5);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_multiply_known" << std::endl;
}

void test_multiply_general() {
    auto A = Mat4::from_rows({1,2,3,4, 5,6,7,8, 9,10,11,12, 13,14,15,16});
    auto B = Mat4::from_rows({17,18,19,20, 21,22,23,24, 25,26,27,28, 29,30,31,32});
    auto R = A.multiply(B);
    // A[0]*B = 1*17+2*21+3*25+4*29 = 17+42+75+116 = 250
    bool ok = close(R.at(0,0), 250);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_multiply_general" << std::endl;
}

void test_determinant_identity() {
    auto I = Mat4::identity();
    bool ok = close(I.determinant(), 1.0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_determinant_identity" << std::endl;
}

void test_determinant_known() {
    auto A = Mat4::from_rows({2,0,0,0, 0,3,0,0, 0,0,4,0, 0,0,0,5});
    bool ok = close(A.determinant(), 120.0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_determinant_known" << std::endl;
}

void test_transpose() {
    auto A = Mat4::from_rows({1,2,3,4, 5,6,7,8, 9,10,11,12, 13,14,15,16});
    auto T = A.transpose();
    bool ok = close(T.at(0,1), 5) && close(T.at(1,0), 2) && close(T.at(2,3), 16);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_transpose" << std::endl;
}

void test_add() {
    auto A = Mat4::from_rows({1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1});
    auto B = A.add(A);
    bool ok = close(B.at(0,0), 2) && close(B.at(3,3), 2);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_add" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_identity_multiply")   test_identity_multiply();
    else if (test == "test_multiply_known")      test_multiply_known();
    else if (test == "test_multiply_general")    test_multiply_general();
    else if (test == "test_determinant_identity") test_determinant_identity();
    else if (test == "test_determinant_known")   test_determinant_known();
    else if (test == "test_transpose")           test_transpose();
    else if (test == "test_add")                 test_add();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
