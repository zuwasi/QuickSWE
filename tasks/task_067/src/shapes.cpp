#include "shapes.h"
#include <cmath>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

Circle::Circle(double radius) : radius_(radius) {}

double Circle::area() const {
    return M_PI * radius_ * radius_;
}

std::string Circle::name() const {
    return "Circle";
}

Rectangle::Rectangle(double width, double height) : width_(width), height_(height) {}

double Rectangle::area() const {
    return width_ * height_;
}

std::string Rectangle::name() const {
    return "Rectangle";
}

/* BUG: returns by value, causing slicing */
Shape ShapeFactory::createShape(const std::string& type, double a, double b) {
    if (type == "circle") {
        Circle c(a);
        return c;  /* SLICED — only Shape part is returned */
    } else if (type == "rectangle") {
        Rectangle r(a, b);
        return r;  /* SLICED */
    }
    return Shape();
}

/* BUG: vector of Shape by value — all elements sliced */
std::string processShapes(std::vector<Shape> shapes) {
    std::ostringstream oss;
    for (size_t i = 0; i < shapes.size(); i++) {
        if (i > 0) oss << ";";
        oss << shapes[i].describe();
    }
    return oss.str();
}
