#pragma once
#include <vector>
#include <stdexcept>
#include <cmath>

class Matrix {
public:
    Matrix(int rows, int cols) : rows_(rows), cols_(cols), data_(rows * cols, 0.0) {}

    int rows() const { return rows_; }
    int cols() const { return cols_; }

    double& at(int r, int c) { return data_[r * cols_ + c]; }
    double  at(int r, int c) const { return data_[r * cols_ + c]; }

    static Matrix identity(int n) {
        Matrix m(n, n);
        for (int i = 0; i < n; ++i) m.at(i, i) = 1.0;
        return m;
    }

    Matrix multiply(const Matrix& other) const {
        if (cols_ != other.rows_)
            throw std::invalid_argument("dimension mismatch");

        Matrix result(rows_, other.cols_);
        for (int i = 0; i < rows_; ++i) {
            for (int j = 0; j < other.cols_; ++j) {
                double sum = 0.0;
                for (int k = 0; k < cols_; ++k) {
                    sum += at(i, k) * other.at(j, k);
                }
                result.at(i, j) = sum;
            }
        }
        return result;
    }

    Matrix transpose() const {
        Matrix result(cols_, rows_);
        for (int i = 0; i < rows_; ++i)
            for (int j = 0; j < cols_; ++j)
                result.at(j, i) = at(i, j);
        return result;
    }

    bool equals(const Matrix& other, double eps = 1e-9) const {
        if (rows_ != other.rows_ || cols_ != other.cols_) return false;
        for (int i = 0; i < rows_ * cols_; ++i)
            if (std::abs(data_[i] - other.data_[i]) > eps) return false;
        return true;
    }

private:
    int rows_, cols_;
    std::vector<double> data_;
};
