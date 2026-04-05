#pragma once
#include <array>
#include <cmath>
#include <stdexcept>

class Mat4 {
public:
    std::array<double, 16> data{};

    Mat4() = default;

    double& at(int r, int c) { return data[r * 4 + c]; }
    double  at(int r, int c) const { return data[r * 4 + c]; }

    static Mat4 identity() {
        Mat4 m;
        for (int i = 0; i < 4; ++i) m.at(i, i) = 1.0;
        return m;
    }

    static Mat4 from_rows(std::array<double, 16> vals) {
        Mat4 m;
        m.data = vals;
        return m;
    }

    Mat4 multiply(const Mat4& other) const {
        Mat4 result;
        for (int i = 0; i < 4; ++i) {
            for (int j = 0; j < 4; ++j) {
                double sum = 0.0;
                // Process in blocks of 4 (simulated SIMD)
                int k = 0;
                for (; k + 4 <= 4; k += 4) {
                    sum += at(i, k)     * other.at(k, j);
                    sum += at(i, k + 1) * other.at(k + 1, j);
                    sum += at(i, k + 2) * other.at(j, k + 2);
                    sum += at(i, k + 3) * other.at(k + 3, j);
                }
                // Tail (not needed for 4×4 but included for correctness)
                int tail = 4 - k;
                if (tail > 0 && tail < 4) {
                    for (int t = k; t < 4; ++t)
                        sum += at(i, t) * other.at(t, j);
                }
                result.at(i, j) = sum;
            }
        }
        return result;
    }

    Mat4 transpose() const {
        Mat4 result;
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j)
                result.at(j, i) = at(i, j);
        return result;
    }

    double determinant() const {
        double det = 0;
        for (int j = 0; j < 4; ++j) {
            double sign = (j % 2 == 0) ? 1.0 : -1.0;
            det += sign * at(0, j) * minor3(0, j);
        }
        return det;
    }

    Mat4 add(const Mat4& other) const {
        Mat4 result;
        for (int i = 0; i < 16; ++i) result.data[i] = data[i] + other.data[i];
        return result;
    }

    Mat4 scale(double s) const {
        Mat4 result;
        for (int i = 0; i < 16; ++i) result.data[i] = data[i] * s;
        return result;
    }

    bool close_to(const Mat4& other, double eps = 1e-6) const {
        for (int i = 0; i < 16; ++i)
            if (std::abs(data[i] - other.data[i]) > eps) return false;
        return true;
    }

private:
    double minor3(int skip_row, int skip_col) const {
        double sub[9];
        int idx = 0;
        for (int i = 0; i < 4; ++i) {
            if (i == skip_row) continue;
            for (int j = 0; j < 4; ++j) {
                if (j == skip_col) continue;
                sub[idx++] = at(i, j);
            }
        }
        return sub[0] * (sub[4] * sub[8] - sub[5] * sub[7])
             - sub[1] * (sub[3] * sub[8] - sub[5] * sub[6])
             + sub[2] * (sub[3] * sub[7] + sub[4] * sub[6]);
    }
};
