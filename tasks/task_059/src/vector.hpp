#pragma once
#include <cstddef>
#include <stdexcept>
#include <algorithm>
#include <initializer_list>

template <typename T>
class Vector {
public:
    using iterator = T*;
    using const_iterator = const T*;

    Vector() : data_(nullptr), size_(0), capacity_(0) {}

    Vector(std::initializer_list<T> init)
        : data_(new T[init.size()]), size_(init.size()), capacity_(init.size()) {
        std::copy(init.begin(), init.end(), data_);
    }

    ~Vector() { delete[] data_; }

    Vector(const Vector& other)
        : data_(new T[other.capacity_]), size_(other.size_), capacity_(other.capacity_) {
        std::copy(other.data_, other.data_ + other.size_, data_);
    }

    Vector& operator=(const Vector& other) {
        if (this != &other) {
            delete[] data_;
            capacity_ = other.capacity_;
            size_ = other.size_;
            data_ = new T[capacity_];
            std::copy(other.data_, other.data_ + size_, data_);
        }
        return *this;
    }

    void push_back(const T& val) {
        if (size_ == capacity_) grow();
        data_[size_++] = val;
    }

    T& operator[](std::size_t i) { return data_[i]; }
    const T& operator[](std::size_t i) const { return data_[i]; }

    std::size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }

    iterator begin() { return data_; }
    iterator end() { return data_ + size_; }
    const_iterator begin() const { return data_; }
    const_iterator end() const { return data_ + size_; }

    iterator erase(iterator pos) {
        if (pos < begin() || pos >= end())
            throw std::out_of_range("erase: iterator out of range");
        std::size_t idx = pos - begin();
        for (std::size_t i = idx; i < size_ - 1; ++i) {
            data_[i] = data_[i + 1];
        }
        --size_;
        return begin() + idx + 1;
    }

    iterator erase(iterator first, iterator last) {
        if (first == last) return first;
        std::size_t start = first - begin();
        std::size_t stop = last - begin();
        std::size_t count = stop - start;
        std::size_t remaining = size_ - stop;
        for (std::size_t i = 0; i < remaining; ++i) {
            data_[start + i] = data_[stop + i];
        }
        size_ -= count - 1;
        return begin() + start;
    }

private:
    T* data_;
    std::size_t size_;
    std::size_t capacity_;

    void grow() {
        std::size_t new_cap = capacity_ == 0 ? 4 : capacity_ * 2;
        T* new_data = new T[new_cap];
        std::copy(data_, data_ + size_, new_data);
        delete[] data_;
        data_ = new_data;
        capacity_ = new_cap;
    }
};
