#include "raytracer.hpp"
#include <iostream>
#include <string>
#include <cmath>

bool close(double a, double b, double eps = 1e-4) { return std::abs(a - b) < eps; }

void test_reflect_basic() {
    Vec3 d(1, -1, 0);
    Vec3 n(0, 1, 0);
    auto r = reflect(d, n);
    // reflect (1,-1,0) off (0,1,0) -> (1,1,0)
    bool ok = close(r.x, 1) && close(r.y, 1) && close(r.z, 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_reflect_basic" << std::endl;
}

void test_reflect_45deg() {
    Vec3 d(0, -1, 0);
    Vec3 n(0, 1, 0);
    auto r = reflect(d, n);
    // Straight down reflected off horizontal -> straight up
    bool ok = close(r.x, 0) && close(r.y, 1) && close(r.z, 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_reflect_45deg" << std::endl;
}

void test_sphere_intersect() {
    Sphere s{{0, 0, -5}, 1.0};
    Ray ray{{0, 0, 0}, {0, 0, -1}};
    auto t = s.intersect(ray);
    bool ok = t.has_value() && close(*t, 4.0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_sphere_intersect" << std::endl;
}

void test_sphere_miss() {
    Sphere s{{0, 0, -5}, 1.0};
    Ray ray{{0, 0, 0}, {0, 1, 0}};
    auto t = s.intersect(ray);
    bool ok = !t.has_value();
    std::cout << (ok ? "PASS" : "FAIL") << ": test_sphere_miss" << std::endl;
}

void test_trace_hit() {
    Sphere s{{0, 0, -5}, 1.0};
    Ray ray{{0, 0, 0}, {0, 0, -1}};
    auto hit = trace(ray, s);
    bool ok = hit.has_value() && close(hit->t, 4.0);
    ok = ok && close(hit->normal.z, 1.0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_trace_hit" << std::endl;
}

void test_nearest_hit() {
    // Ray should hit the nearest point, not the farther one
    Sphere s{{0, 0, -3}, 1.0};
    Ray ray{{0, 0, 0}, {0, 0, -1}};
    auto t = s.intersect(ray);
    bool ok = t.has_value() && close(*t, 2.0);  // nearest is at t=2
    std::cout << (ok ? "PASS" : "FAIL") << ": test_nearest_hit" << std::endl;
}

void test_vec3_normalize() {
    Vec3 v(3, 4, 0);
    auto n = v.normalize();
    bool ok = close(n.x, 0.6) && close(n.y, 0.8) && close(n.z, 0);
    std::cout << (ok ? "PASS" : "FAIL") << ": test_vec3_normalize" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_reflect_basic")     test_reflect_basic();
    else if (test == "test_reflect_45deg")     test_reflect_45deg();
    else if (test == "test_sphere_intersect")  test_sphere_intersect();
    else if (test == "test_sphere_miss")       test_sphere_miss();
    else if (test == "test_trace_hit")         test_trace_hit();
    else if (test == "test_nearest_hit")       test_nearest_hit();
    else if (test == "test_vec3_normalize")    test_vec3_normalize();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
