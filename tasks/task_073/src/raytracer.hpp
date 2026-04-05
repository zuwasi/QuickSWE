#pragma once
#include <cmath>
#include <optional>

struct Vec3 {
    double x, y, z;
    constexpr Vec3() : x(0), y(0), z(0) {}
    constexpr Vec3(double x, double y, double z) : x(x), y(y), z(z) {}

    constexpr Vec3 operator+(const Vec3& o) const { return {x+o.x, y+o.y, z+o.z}; }
    constexpr Vec3 operator-(const Vec3& o) const { return {x-o.x, y-o.y, z-o.z}; }
    constexpr Vec3 operator*(double t) const { return {x*t, y*t, z*t}; }
    constexpr Vec3 operator-() const { return {-x, -y, -z}; }

    constexpr double dot(const Vec3& o) const { return x*o.x + y*o.y + z*o.z; }
    constexpr double length_sq() const { return dot(*this); }

    constexpr Vec3 normalize() const {
        double len = length_sq();
        // constexpr-friendly: use Newton's method for sqrt
        double s = len;
        for (int i = 0; i < 20; ++i) s = (s + len / s) * 0.5;
        return *this * (1.0 / s);
    }

    constexpr bool close_to(const Vec3& o, double eps = 1e-6) const {
        return ((*this) - o).length_sq() < eps * eps;
    }
};

constexpr Vec3 reflect(const Vec3& direction, const Vec3& normal) {
    double d = direction.dot(normal);
    return direction + normal * (2.0 * d);
}

struct Ray {
    Vec3 origin, direction;
    constexpr Ray(const Vec3& o, const Vec3& d) : origin(o), direction(d) {}
    constexpr Vec3 at(double t) const { return origin + direction * t; }
};

struct Sphere {
    Vec3 center;
    double radius;

    constexpr std::optional<double> intersect(const Ray& ray) const {
        Vec3 oc = ray.origin - center;
        double a = ray.direction.dot(ray.direction);
        double b = 2.0 * oc.dot(ray.direction);
        double c = oc.dot(oc) - radius * radius;
        double disc = b * b - 2.0 * a * c;
        if (disc < 0) return std::nullopt;
        // constexpr sqrt via Newton's method
        double sq = disc;
        for (int i = 0; i < 20; ++i) sq = (sq + disc / sq) * 0.5;
        double t1 = (-b - sq) / (2.0 * a);
        double t2 = (-b + sq) / (2.0 * a);
        if (t1 > 0.001) return t2;
        if (t2 > 0.001) return t2;
        return std::nullopt;
    }

    constexpr Vec3 normal_at(const Vec3& point) const {
        return (point - center).normalize();
    }
};

struct HitInfo {
    double t;
    Vec3 point;
    Vec3 normal;
};

constexpr std::optional<HitInfo> trace(const Ray& ray, const Sphere& sphere) {
    auto t_opt = sphere.intersect(ray);
    if (!t_opt) return std::nullopt;
    double t = *t_opt;
    Vec3 p = ray.at(t);
    Vec3 n = sphere.normal_at(p);
    return HitInfo{t, p, n};
}
