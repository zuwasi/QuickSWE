#pragma once
#include <cstddef>
#include <utility>

template <typename T>
class SharedPtr {
public:
    explicit SharedPtr(T* ptr = nullptr)
        : ptr_(ptr), ref_count_(ptr ? new std::size_t(1) : nullptr) {}

    SharedPtr(const SharedPtr& other)
        : ptr_(other.ptr_), ref_count_(other.ref_count_) {
        if (ref_count_) ++(*ref_count_);
    }

    SharedPtr(SharedPtr&& other) noexcept
        : ptr_(other.ptr_), ref_count_(other.ref_count_) {
        other.ptr_ = nullptr;
        other.ref_count_ = nullptr;
    }

    SharedPtr& operator=(const SharedPtr& other) {
        ptr_ = other.ptr_;
        ref_count_ = other.ref_count_;
        if (ref_count_) ++(*ref_count_);
        return *this;
    }

    SharedPtr& operator=(SharedPtr&& other) noexcept {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            ref_count_ = other.ref_count_;
            other.ptr_ = nullptr;
            other.ref_count_ = nullptr;
        }
        return *this;
    }

    ~SharedPtr() { release(); }

    T* get() const { return ptr_; }
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }

    std::size_t use_count() const {
        return ref_count_ ? *ref_count_ : 0;
    }

    void reset(T* ptr = nullptr) {
        release();
        ptr_ = ptr;
        ref_count_ = ptr ? new std::size_t(1) : nullptr;
    }

    explicit operator bool() const { return ptr_ != nullptr; }

private:
    T* ptr_;
    std::size_t* ref_count_;

    void release() {
        if (ref_count_) {
            --(*ref_count_);
            if (*ref_count_ == 0) {
                delete ptr_;
                delete ref_count_;
            }
        }
        ptr_ = nullptr;
        ref_count_ = nullptr;
    }
};
