#pragma once
#include <atomic>
#include <optional>
#include <cstdint>
#include <vector>

template <typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
        Node(const T& val) : data(val), next(nullptr) {}
    };

    struct TaggedPtr {
        Node* ptr;
        std::size_t tag;
        TaggedPtr() : ptr(nullptr), tag(0) {}
        TaggedPtr(Node* p, std::size_t t) : ptr(p), tag(t) {}
        bool operator==(const TaggedPtr& o) const {
            return ptr == o.ptr && tag == o.tag;
        }
    };

    // Using a simple struct + atomic for portability
    // In real code you'd use a double-width CAS
    struct AtomicTaggedPtr {
        std::atomic<Node*> ptr{nullptr};
        std::atomic<std::size_t> tag{0};

        TaggedPtr load() const {
            return {ptr.load(std::memory_order_acquire),
                    tag.load(std::memory_order_acquire)};
        }

        bool cas(TaggedPtr& expected, TaggedPtr desired) {
            Node* exp_ptr = expected.ptr;
            if (ptr.compare_exchange_strong(exp_ptr, desired.ptr,
                    std::memory_order_acq_rel)) {
                tag.store(desired.tag, std::memory_order_release);
                return true;
            }
            expected.ptr = exp_ptr;
            expected.tag = tag.load(std::memory_order_acquire);
            return false;
        }
    };

public:
    LockFreeStack() = default;

    ~LockFreeStack() {
        while (pop().has_value()) {}
    }

    void push(const T& value) {
        Node* node = new Node(value);
        TaggedPtr old_head = head_.load();
        node->next = old_head.ptr;
        TaggedPtr new_head(node, old_head.tag);
        while (!head_.cas(old_head, new_head)) {
            node->next = old_head.ptr;
            new_head = TaggedPtr(node, old_head.tag);
        }
    }

    std::optional<T> pop() {
        TaggedPtr old_head = head_.load();
        while (old_head.ptr) {
            TaggedPtr new_head(old_head.ptr->next, old_head.tag + 1);
            if (head_.cas(old_head, new_head)) {
                T val = old_head.ptr->data;
                delete old_head.ptr;
                return val;
            }
        }
        return std::nullopt;
    }

    bool empty() const {
        return head_.load().ptr == nullptr;
    }

    std::vector<T> drain() {
        std::vector<T> result;
        while (auto val = pop()) {
            result.push_back(*val);
        }
        return result;
    }

    std::size_t size() const {
        std::size_t count = 0;
        Node* curr = head_.load().ptr;
        while (curr) {
            ++count;
            curr = curr->next;
        }
        return count;
    }

private:
    AtomicTaggedPtr head_;
};
