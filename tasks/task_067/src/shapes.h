#ifndef SHAPES_H
#define SHAPES_H

#include <string>
#include <vector>
#include <memory>

class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const { return 0.0; }
    virtual std::string name() const { return "Shape"; }
    virtual std::string describe() const {
        return name() + ":area=" + std::to_string(area());
    }
};

class Circle : public Shape {
public:
    Circle(double radius);
    double area() const override;
    std::string name() const override;

private:
    double radius_;
};

class Rectangle : public Shape {
public:
    Rectangle(double width, double height);
    double area() const override;
    std::string name() const override;

private:
    double width_;
    double height_;
};

class ShapeFactory {
public:
    /* BUG: returns Shape by value — causes object slicing */
    static Shape createShape(const std::string& type, double a, double b = 0.0);
};

/* BUG: takes and stores Shape by value — slicing */
std::string processShapes(std::vector<Shape> shapes);

#endif
