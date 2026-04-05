#pragma once
#include <array>
#include <cstddef>
#include <stdexcept>
#include <vector>

template <typename T, std::size_t N>
class CircularBuffer {
public:
    CircularBuffer() : head_(0), tail_(0), count_(0) {}

    void push_back(const T& value) {
        buf_[tail_] = value;
        tail_ = (tail_ + 1) % N;
        if (count_ == N) {
            head_ = tail_;
        } else {
            count_++;
        }
    }

    T pop_front() {
        if (empty()) throw std::runtime_error("pop from empty buffer");
        T val = buf_[head_];
        head_ = (head_ + 1) % N;
        count_--;
        return val;
    }

    T front() const {
        if (empty()) throw std::runtime_error("front on empty buffer");
        return buf_[head_];
    }

    T back() const {
        if (empty()) throw std::runtime_error("back on empty buffer");
        std::size_t idx = (tail_ == 0) ? N - 1 : tail_ - 1;
        return buf_[idx];
    }

    bool empty() const { return count_ == 0; }
    bool full()  const { return count_ == N; }

    std::size_t size() const {
        if (tail_ >= head_)
            return tail_ - head_;
        return N - head_ + tail_;
    }

    std::vector<T> to_vector() const {
        std::vector<T> result;
        for (std::size_t i = 0; i < size(); ++i) {
            result.push_back(buf_[(head_ + i) % N]);
        }
        return result;
    }

private:
    std::array<T, N> buf_{};
    std::size_t head_;
    std::size_t tail_;
    std::size_t count_;
};
