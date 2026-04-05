#pragma once
#include <vector>
#include <algorithm>
#include <iostream>
#include <cassert>

class BPlusTree {
    static constexpr int ORDER = 4;
    static constexpr int MIN_KEYS = (ORDER - 1) / 2;

    struct Node {
        bool is_leaf;
        std::vector<int> keys;
        std::vector<Node*> children;
        Node* next;  // leaf linked list
        Node* parent;

        Node(bool leaf) : is_leaf(leaf), next(nullptr), parent(nullptr) {}
    };

public:
    BPlusTree() : root_(new Node(true)), size_(0) {}

    ~BPlusTree() { destroy(root_); }

    void insert(int key) {
        Node* leaf = find_leaf(key);
        auto it = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key);
        if (it != leaf->keys.end() && *it == key) return;
        leaf->keys.insert(it, key);
        ++size_;
        if ((int)leaf->keys.size() >= ORDER) split_leaf(leaf);
    }

    bool search(int key) const {
        Node* leaf = find_leaf(key);
        auto it = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key);
        return it != leaf->keys.end() && *it == key;
    }

    std::vector<int> range_query(int low, int high) const {
        std::vector<int> result;
        Node* leaf = find_leaf(low);
        while (leaf) {
            for (int k : leaf->keys) {
                if (k >= low && k <= high) result.push_back(k);
                if (k > high) return result;
            }
            leaf = leaf->next;
        }
        return result;
    }

    bool remove(int key) {
        Node* leaf = find_leaf(key);
        auto it = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key);
        if (it == leaf->keys.end() || *it != key) return false;
        leaf->keys.erase(it);
        --size_;
        if (leaf == root_) return true;
        if ((int)leaf->keys.size() < MIN_KEYS) fix_underflow(leaf);
        return true;
    }

    std::size_t size() const { return size_; }

    std::vector<int> all_keys() const {
        std::vector<int> result;
        Node* leaf = root_;
        while (!leaf->is_leaf) leaf = leaf->children[0];
        while (leaf) {
            for (int k : leaf->keys) result.push_back(k);
            leaf = leaf->next;
        }
        return result;
    }

private:
    Node* root_;
    std::size_t size_;

    void destroy(Node* node) {
        if (!node) return;
        if (!node->is_leaf)
            for (auto* c : node->children) destroy(c);
        delete node;
    }

    Node* find_leaf(int key) const {
        Node* curr = root_;
        while (!curr->is_leaf) {
            int i = (int)(std::upper_bound(curr->keys.begin(), curr->keys.end(), key)
                          - curr->keys.begin());
            curr = curr->children[i];
        }
        return curr;
    }

    void split_leaf(Node* leaf) {
        int mid = ORDER / 2;
        Node* new_leaf = new Node(true);
        new_leaf->keys.assign(leaf->keys.begin() + mid, leaf->keys.end());
        leaf->keys.resize(mid);
        new_leaf->next = leaf->next;
        leaf->next = new_leaf;
        int up_key = new_leaf->keys[0];
        insert_into_parent(leaf, up_key, new_leaf);
    }

    void split_internal(Node* node) {
        int mid = (int)node->keys.size() / 2;
        int up_key = node->keys[mid];
        Node* new_node = new Node(false);
        new_node->keys.assign(node->keys.begin() + mid + 1, node->keys.end());
        new_node->children.assign(node->children.begin() + mid + 1, node->children.end());
        for (auto* c : new_node->children) c->parent = new_node;
        node->keys.resize(mid);
        node->children.resize(mid + 1);
        insert_into_parent(node, up_key, new_node);
    }

    void insert_into_parent(Node* left, int key, Node* right) {
        if (!left->parent) {
            Node* new_root = new Node(false);
            new_root->keys.push_back(key);
            new_root->children.push_back(left);
            new_root->children.push_back(right);
            left->parent = new_root;
            right->parent = new_root;
            root_ = new_root;
            return;
        }
        Node* parent = left->parent;
        right->parent = parent;
        auto it = std::lower_bound(parent->keys.begin(), parent->keys.end(), key);
        int idx = (int)(it - parent->keys.begin());
        parent->keys.insert(it, key);
        parent->children.insert(parent->children.begin() + idx + 1, right);
        if ((int)parent->keys.size() >= ORDER) split_internal(parent);
    }

    void fix_underflow(Node* node) {
        Node* parent = node->parent;
        int idx = child_index(parent, node);

        // Try borrow from left sibling
        if (idx > 0) {
            Node* left_sib = parent->children[idx - 1];
            if ((int)left_sib->keys.size() > MIN_KEYS) {
                redistribute_from_left(parent, idx);
                return;
            }
        }
        // Try borrow from right sibling
        if (idx < (int)parent->children.size() - 1) {
            Node* right_sib = parent->children[idx + 1];
            if ((int)right_sib->keys.size() > MIN_KEYS) {
                redistribute_from_right(parent, idx);
                return;
            }
        }
        // Merge
        if (idx > 0) merge(parent, idx - 1);
        else merge(parent, idx);
    }

    void redistribute_from_left(Node* parent, int idx) {
        Node* node = parent->children[idx];
        Node* left = parent->children[idx - 1];
        if (node->is_leaf) {
            int borrowed = left->keys.back();
            left->keys.pop_back();
            node->keys.insert(node->keys.begin(), borrowed);
            parent->keys[idx - 1] = borrowed;
        } else {
            node->keys.insert(node->keys.begin(), parent->keys[idx - 1]);
            parent->keys[idx - 1] = left->keys.back();
            left->keys.pop_back();
            node->children.insert(node->children.begin(), left->children.back());
            node->children[0]->parent = node;
            left->children.pop_back();
        }
    }

    void redistribute_from_right(Node* parent, int idx) {
        Node* node = parent->children[idx];
        Node* right = parent->children[idx + 1];
        if (node->is_leaf) {
            int borrowed = right->keys.front();
            right->keys.erase(right->keys.begin());
            node->keys.push_back(borrowed);
            parent->keys[idx] = borrowed;
        } else {
            node->keys.push_back(parent->keys[idx]);
            parent->keys[idx] = right->keys.front();
            right->keys.erase(right->keys.begin());
            node->children.push_back(right->children.front());
            node->children.back()->parent = node;
            right->children.erase(right->children.begin());
        }
    }

    void merge(Node* parent, int idx) {
        Node* left = parent->children[idx];
        Node* right = parent->children[idx + 1];
        if (!left->is_leaf) {
            left->keys.push_back(parent->keys[idx]);
        }
        for (int k : right->keys) left->keys.push_back(k);
        if (!left->is_leaf) {
            for (auto* c : right->children) {
                left->children.push_back(c);
                c->parent = left;
            }
        }
        if (left->is_leaf) left->next = right->next;
        parent->keys.erase(parent->keys.begin() + idx);
        parent->children.erase(parent->children.begin() + idx + 1);
        delete right;

        if (parent == root_ && parent->keys.empty()) {
            root_ = left;
            left->parent = nullptr;
            delete parent;
        } else if (parent != root_ && (int)parent->keys.size() < MIN_KEYS) {
            fix_underflow(parent);
        }
    }

    int child_index(Node* parent, Node* child) {
        for (int i = 0; i < (int)parent->children.size(); ++i)
            if (parent->children[i] == child) return i;
        return -1;
    }
};
