#include <iostream>
#include <string>
#include <cstring>
#include <cmath>
#include <vector>
#include "shapes.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: prog <test_name>" << std::endl;
        return 1;
    }

    std::string test = argv[1];

    if (test == "factory_circle") {
        auto shape = ShapeFactory::createShape("circle", 5.0);
        std::cout << "name=" << shape.name() << std::endl;
        std::cout << "area=" << (int)round(shape.area()) << std::endl;
    }
    else if (test == "factory_rectangle") {
        auto shape = ShapeFactory::createShape("rectangle", 4.0, 6.0);
        std::cout << "name=" << shape.name() << std::endl;
        std::cout << "area=" << (int)round(shape.area()) << std::endl;
    }
    else if (test == "process_shapes") {
        std::vector<Shape> shapes;
        Circle c(3.0);
        Rectangle r(2.0, 5.0);
        shapes.push_back(c);  /* sliced */
        shapes.push_back(r);  /* sliced */
        std::string result = processShapes(shapes);
        std::cout << result << std::endl;
    }
    else if (test == "direct_circle") {
        /* Direct usage without factory — no slicing */
        Circle c(5.0);
        std::cout << "name=" << c.name() << std::endl;
        std::cout << "area=" << (int)round(c.area()) << std::endl;
    }
    else if (test == "direct_rectangle") {
        Rectangle r(4.0, 6.0);
        std::cout << "name=" << r.name() << std::endl;
        std::cout << "area=" << (int)round(r.area()) << std::endl;
    }
    else {
        std::cout << "Unknown test: " << test << std::endl;
        return 1;
    }

    return 0;
}
