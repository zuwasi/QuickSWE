#include <iostream>
#include <string>
#include <cstring>
#include "type_traits.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: prog <test_name>" << std::endl;
        return 1;
    }

    std::string test = argv[1];

    if (test == "is_same_basic") {
        static_assert(my_is_same<int, int>::value, "int == int");
        static_assert(!my_is_same<int, float>::value, "int != float");
        static_assert(my_is_same<const int, const int>::value, "const int == const int");
        std::cout << "is_same_basic=PASS" << std::endl;
    }
    else if (test == "is_pointer_basic") {
        static_assert(my_is_pointer<int*>::value, "int* is pointer");
        static_assert(!my_is_pointer<int>::value, "int is not pointer");
        static_assert(my_is_pointer<double*>::value, "double* is pointer");
        std::cout << "is_pointer_basic=PASS" << std::endl;
    }
    else if (test == "is_pointer_cv_qualified") {
        /*
         * BUG: these static_asserts fail because my_is_pointer<T*> doesn't
         * match cv-qualified pointer types like int* const.
         * int* const  = const pointer to int (the pointer itself is const)
         * const int*  = pointer to const int (this one works with T* where T=const int)
         */
        static_assert(my_is_pointer<int* const>::value, "int* const is pointer");
        static_assert(my_is_pointer<int* volatile>::value, "int* volatile is pointer");
        static_assert(my_is_pointer<int* const volatile>::value, "int* const volatile is pointer");
        std::cout << "is_pointer_cv=PASS" << std::endl;
    }
    else if (test == "is_const_basic") {
        static_assert(my_is_const<const int>::value, "const int is const");
        static_assert(!my_is_const<int>::value, "int is not const");
        std::cout << "is_const_basic=PASS" << std::endl;
    }
    else if (test == "remove_const_basic") {
        static_assert(my_is_same<my_remove_const<const int>::type, int>::value, "remove_const<const int> == int");
        static_assert(my_is_same<my_remove_const<int>::type, int>::value, "remove_const<int> == int");
        std::cout << "remove_const_basic=PASS" << std::endl;
    }
    else if (test == "remove_const_volatile") {
        /* BUG: this will fail because my_remove_const<const volatile int>
         * doesn't have a specialization, so type remains const volatile int */
        static_assert(
            my_is_same<my_remove_const<const volatile int>::type, volatile int>::value,
            "remove_const<const volatile int> == volatile int"
        );
        std::cout << "remove_const_volatile=PASS" << std::endl;
    }
    else if (test == "remove_pointer_cv") {
        /* BUG: my_remove_pointer<int* const> doesn't strip the pointer */
        static_assert(
            my_is_same<my_remove_pointer<int* const>::type, int>::value,
            "remove_pointer<int* const> == int"
        );
        std::cout << "remove_pointer_cv=PASS" << std::endl;
    }
    else {
        std::cout << "Unknown test: " << test << std::endl;
        return 1;
    }

    return 0;
}
