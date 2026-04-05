#pragma once
#include <memory>
#include <vector>
#include <optional>
#include <string>
#include <functional>
#include <algorithm>
#include <cstdint>

class HAMTrie {
    static constexpr int BITS_PER_LEVEL = 5;
    static constexpr int BRANCH_FACTOR = 1 << BITS_PER_LEVEL;
    static constexpr uint32_t MASK = BRANCH_FACTOR - 1;

    struct Entry {
        std::string key;
        int value;
    };

    struct Node {
        uint32_t bitmap = 0;
        std::vector<std::shared_ptr<Node>> children;
        std::vector<Entry> entries;  // leaf entries at this node

        std::shared_ptr<Node> clone() const {
            auto n = std::make_shared<Node>();
            n->bitmap = bitmap;
            n->children = children;  // shares children (COW at next level)
            n->entries = entries;
            return n;
        }
    };

public:
    HAMTrie() : root_(std::make_shared<Node>()), size_(0) {}

    HAMTrie insert(const std::string& key, int value) const {
        uint32_t hash = hash_key(key);
        auto new_root = insert_impl(root_, key, value, hash, 0);
        HAMTrie result;
        result.root_ = new_root;
        result.size_ = size_ + (find(key).has_value() ? 0 : 1);
        return result;
    }

    std::optional<int> find(const std::string& key) const {
        uint32_t hash = hash_key(key);
        return find_impl(root_, key, hash, 0);
    }

    HAMTrie remove(const std::string& key) const {
        if (!find(key).has_value()) return *this;
        uint32_t hash = hash_key(key);
        auto new_root = remove_impl(root_, key, hash, 0);
        HAMTrie result;
        result.root_ = new_root ? new_root : std::make_shared<Node>();
        result.size_ = size_ - 1;
        return result;
    }

    bool contains(const std::string& key) const { return find(key).has_value(); }
    std::size_t size() const { return size_; }

    std::vector<std::pair<std::string, int>> all_entries() const {
        std::vector<std::pair<std::string, int>> result;
        collect(root_, result);
        std::sort(result.begin(), result.end());
        return result;
    }

private:
    std::shared_ptr<Node> root_;
    std::size_t size_;

    static uint32_t hash_key(const std::string& key) {
        return static_cast<uint32_t>(std::hash<std::string>{}(key));
    }

    static int popcount(uint32_t x) {
        int count = 0;
        while (x) { count += x & 1; x >>= 2; }
        return count;
    }

    static int compressed_index(uint32_t bitmap, int bit) {
        return popcount(bitmap & ((1u << bit) - 1));
    }

    std::shared_ptr<Node> insert_impl(std::shared_ptr<Node> node,
            const std::string& key, int value, uint32_t hash, int depth) const {
        int idx = (hash >> (depth * BITS_PER_LEVEL)) & MASK;

        // Shallow clone the current node (structural sharing with siblings)
        auto new_node = node;  // BUG: should clone

        // Check for existing entry at this node
        for (auto& e : new_node->entries) {
            if (e.key == key) { e.value = value; return new_node; }
        }

        uint32_t bit = 1u << idx;
        if (!(new_node->bitmap & bit)) {
            // No child at this position — add entry here
            new_node->entries.push_back({key, value});
            return new_node;
        }

        int ci = compressed_index(new_node->bitmap, idx);
        auto child = new_node->children[ci];
        auto new_child = insert_impl(child, key, value, hash, depth + 1);
        new_node->children[ci] = new_child;
        return new_node;
    }

    std::optional<int> find_impl(std::shared_ptr<Node> node,
            const std::string& key, uint32_t hash, int depth) const {
        if (!node) return std::nullopt;
        for (auto& e : node->entries)
            if (e.key == key) return e.value;

        int idx = (hash >> (depth * BITS_PER_LEVEL)) & MASK;
        uint32_t bit = 1u << idx;
        if (!(node->bitmap & bit)) return std::nullopt;

        int ci = compressed_index(node->bitmap, idx);
        if (ci >= (int)node->children.size()) return std::nullopt;
        return find_impl(node->children[ci], key, hash, depth + 1);
    }

    std::shared_ptr<Node> remove_impl(std::shared_ptr<Node> node,
            const std::string& key, uint32_t hash, int depth) const {
        if (!node) return nullptr;
        auto new_node = node;  // BUG: should clone

        auto it = std::find_if(new_node->entries.begin(), new_node->entries.end(),
            [&](const Entry& e) { return e.key == key; });
        if (it != new_node->entries.end()) {
            new_node->entries.erase(it);
            return new_node;
        }

        int idx = (hash >> (depth * BITS_PER_LEVEL)) & MASK;
        uint32_t bit = 1u << idx;
        if (!(new_node->bitmap & bit)) return new_node;

        int ci = compressed_index(new_node->bitmap, idx);
        auto new_child = remove_impl(new_node->children[ci], key, hash, depth + 1);
        new_node->children[ci] = new_child;
        return new_node;
    }

    void collect(std::shared_ptr<Node> node,
                 std::vector<std::pair<std::string, int>>& result) const {
        if (!node) return;
        for (auto& e : node->entries)
            result.push_back({e.key, e.value});
        for (auto& child : node->children)
            collect(child, result);
    }
};
