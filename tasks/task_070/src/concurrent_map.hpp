#pragma once
#include <atomic>
#include <vector>
#include <optional>
#include <functional>
#include <string>

template <typename K, typename V>
class ConcurrentMap {
    struct Node {
        K key;
        V value;
        std::atomic<bool> deleted{false};
        std::atomic<Node*> next{nullptr};
        Node(const K& k, const V& v) : key(k), value(v) {}
    };

public:
    explicit ConcurrentMap(std::size_t bucket_count = 16)
        : buckets_(bucket_count), size_(0) {
        for (auto& b : buckets_) b.store(nullptr, std::memory_order_relaxed);
    }

    ~ConcurrentMap() {
        for (auto& b : buckets_) {
            Node* curr = b.load(std::memory_order_relaxed);
            while (curr) {
                Node* next = curr->next.load(std::memory_order_relaxed);
                delete curr;
                curr = next;
            }
        }
    }

    void insert(const K& key, const V& value) {
        std::size_t idx = bucket_for(key);
        Node* node = new Node(key, value);

        Node* head = buckets_[idx].load(std::memory_order_relaxed);
        // Check for existing key
        Node* curr = head;
        while (curr) {
            if (!curr->deleted.load(std::memory_order_relaxed) && curr->key == key) {
                curr->value = value;
                delete node;
                return;
            }
            curr = curr->next.load(std::memory_order_relaxed);
        }

        node->next.store(head, std::memory_order_relaxed);
        buckets_[idx].store(node, std::memory_order_relaxed);
        size_.fetch_add(1, std::memory_order_relaxed);
    }

    std::optional<V> find(const K& key) const {
        std::size_t idx = bucket_for(key);
        Node* curr = buckets_[idx].load(std::memory_order_relaxed);
        while (curr) {
            if (!curr->deleted.load(std::memory_order_relaxed) && curr->key == key)
                return curr->value;
            curr = curr->next.load(std::memory_order_relaxed);
        }
        return std::nullopt;
    }

    bool remove(const K& key) {
        std::size_t idx = bucket_for(key);
        Node* curr = buckets_[idx].load(std::memory_order_relaxed);
        while (curr) {
            if (!curr->deleted.load(std::memory_order_relaxed) && curr->key == key) {
                curr->deleted.store(true, std::memory_order_relaxed);
                size_.fetch_sub(1, std::memory_order_relaxed);
                return true;
            }
            curr = curr->next.load(std::memory_order_relaxed);
        }
        return false;
    }

    std::size_t size() const {
        return size_.load(std::memory_order_relaxed);
    }

    bool contains(const K& key) const {
        return find(key).has_value();
    }

    std::vector<std::pair<K,V>> all_entries() const {
        std::vector<std::pair<K,V>> result;
        for (const auto& b : buckets_) {
            Node* curr = b.load(std::memory_order_relaxed);
            while (curr) {
                if (!curr->deleted.load(std::memory_order_relaxed))
                    result.push_back({curr->key, curr->value});
                curr = curr->next.load(std::memory_order_relaxed);
            }
        }
        return result;
    }

private:
    std::vector<std::atomic<Node*>> buckets_;
    std::atomic<std::size_t> size_;

    std::size_t bucket_for(const K& key) const {
        return std::hash<K>{}(key) % buckets_.size();
    }
};
