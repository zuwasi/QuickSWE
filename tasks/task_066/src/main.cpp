#include <iostream>
#include <string>
#include <cstring>
#include "skiplist.h"

/* These will only compile after iterator support is added */
#ifdef HAS_ITERATOR
#include <algorithm>
#endif

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: prog <test_name>" << std::endl;
        return 1;
    }

    std::string test = argv[1];

    if (test == "basic_ops") {
        SkipList<int> sl;
        sl.insert(30);
        sl.insert(10);
        sl.insert(20);
        std::cout << "size=" << sl.size() << std::endl;
        std::cout << "contains_10=" << sl.contains(10) << std::endl;
        std::cout << "contains_40=" << sl.contains(40) << std::endl;
        sl.print();
    }
    else if (test == "range_for") {
#ifdef HAS_ITERATOR
        SkipList<int> sl;
        sl.insert(50);
        sl.insert(10);
        sl.insert(30);
        sl.insert(20);
        sl.insert(40);

        bool first = true;
        for (const auto& val : sl) {
            if (!first) std::cout << " ";
            std::cout << val;
            first = false;
        }
        std::cout << std::endl;
#else
        std::cout << "NOT_IMPLEMENTED" << std::endl;
#endif
    }
    else if (test == "std_find") {
#ifdef HAS_ITERATOR
        SkipList<int> sl;
        sl.insert(100);
        sl.insert(200);
        sl.insert(300);

        auto it = std::find(sl.begin(), sl.end(), 200);
        if (it != sl.end()) {
            std::cout << "found=" << *it << std::endl;
        } else {
            std::cout << "found=NONE" << std::endl;
        }

        auto it2 = std::find(sl.begin(), sl.end(), 999);
        std::cout << "not_found=" << (it2 == sl.end() ? "true" : "false") << std::endl;
#else
        std::cout << "NOT_IMPLEMENTED" << std::endl;
#endif
    }
    else if (test == "std_count_if") {
#ifdef HAS_ITERATOR
        SkipList<int> sl;
        sl.insert(5);
        sl.insert(15);
        sl.insert(25);
        sl.insert(3);
        sl.insert(8);

        int count = std::count_if(sl.begin(), sl.end(), [](int v) { return v > 10; });
        std::cout << "count_gt_10=" << count << std::endl;
#else
        std::cout << "NOT_IMPLEMENTED" << std::endl;
#endif
    }
    else if (test == "remove_and_iterate") {
#ifdef HAS_ITERATOR
        SkipList<int> sl;
        sl.insert(1);
        sl.insert(2);
        sl.insert(3);
        sl.insert(4);
        sl.remove(2);

        bool first = true;
        for (const auto& val : sl) {
            if (!first) std::cout << " ";
            std::cout << val;
            first = false;
        }
        std::cout << std::endl;
#else
        std::cout << "NOT_IMPLEMENTED" << std::endl;
#endif
    }
    else {
        std::cout << "Unknown test: " << test << std::endl;
        return 1;
    }

    return 0;
}
