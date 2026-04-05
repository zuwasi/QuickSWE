#pragma once
#include <vector>
#include <stdexcept>
#include <algorithm>

template <typename T>
class MinHeap {
public:
    void push(const T& value) {
        data_.push_back(value);
        sift_up(data_.size() - 1);
    }

    T pop() {
        if (data_.empty()) throw std::runtime_error("pop from empty heap");
        T val = data_[0];
        data_[0] = data_.back();
        data_.pop_back();
        if (!data_.empty()) sift_down(0);
        return val;
    }

    const T& top() const {
        if (data_.empty()) throw std::runtime_error("top on empty heap");
        return data_[0];
    }

    std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }

    std::vector<T> sorted_extract() {
        std::vector<T> result;
        while (!empty()) result.push_back(pop());
        return result;
    }

private:
    std::vector<T> data_;

    void sift_up(std::size_t idx) {
        while (idx > 0) {
            std::size_t parent = (idx - 1) / 2;
            if (data_[idx] < data_[parent]) {
                std::swap(data_[idx], data_[parent]);
                idx = parent;
            } else {
                break;
            }
        }
    }

    void sift_down(std::size_t idx) {
        std::size_t n = data_.size();
        std::size_t left = 2 * idx + 1;
        if (left >= n) return;
        std::size_t right = 2 * idx + 2;
        std::size_t smallest = idx;

        if (data_[left] < data_[smallest])
            smallest = left;
        if (right < n && data_[right] < data_[smallest])
            smallest = right;

        if (smallest != idx) {
            std::swap(data_[idx], data_[smallest]);
        }
    }
};
