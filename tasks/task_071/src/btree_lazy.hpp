#pragma once
#include <vector>
#include <algorithm>
#include <optional>

class BTreeLazy {
    static constexpr int ORDER = 3;
    static constexpr int MAX_KEYS = ORDER - 1;
    static constexpr int MIN_KEYS = (ORDER - 1) / 2;

    struct Entry {
        int key;
        bool deleted;
        Entry(int k) : key(k), deleted(false) {}
    };

    struct Node {
        std::vector<Entry> entries;
        std::vector<Node*> children;
        bool is_leaf;
        Node(bool leaf) : is_leaf(leaf) {}
        ~Node() { for (auto* c : children) delete c; }
    };

public:
    BTreeLazy() : root_(new Node(true)) {}
    ~BTreeLazy() { delete root_; }

    void insert(int key) {
        if (root_->entries.size() == MAX_KEYS) {
            Node* new_root = new Node(false);
            new_root->children.push_back(root_);
            split_child(new_root, 0);
            root_ = new_root;
        }
        insert_non_full(root_, key);
    }

    bool search(int key) const {
        return search_impl(root_, key);
    }

    bool lazy_remove(int key) {
        return mark_deleted(root_, key);
    }

    void compact() {
        std::vector<int> live_keys;
        collect_live(root_, live_keys);
        std::sort(live_keys.begin(), live_keys.end());
        delete root_;
        root_ = new Node(true);
        for (int k : live_keys) {
            if (root_->entries.size() == MAX_KEYS) {
                Node* new_root = new Node(false);
                new_root->children.push_back(root_);
                split_child(new_root, 0);
                root_ = new_root;
            }
            insert_non_full(root_, k);
        }
    }

    std::vector<int> inorder() const {
        std::vector<int> result;
        inorder_impl(root_, result);
        return result;
    }

    int active_count() const {
        int count = 0;
        count_active(root_, count);
        return count;
    }

private:
    Node* root_;

    void split_child(Node* parent, int idx) {
        Node* child = parent->children[idx];
        int mid = MAX_KEYS / 2;
        Node* sibling = new Node(child->is_leaf);

        // Move upper half of entries to sibling
        for (int i = mid + 1; i < (int)child->entries.size(); ++i)
            sibling->entries.push_back(child->entries[i]);

        if (!child->is_leaf) {
            for (int i = mid + 1; i < (int)child->children.size(); ++i)
                sibling->children.push_back(child->children[i]);
            child->children.resize(mid + 1);
        }

        Entry up = child->entries[mid];
        child->entries.resize(mid);

        parent->entries.insert(parent->entries.begin() + idx, up);
        parent->children.insert(parent->children.begin() + idx + 1, sibling);
    }

    void insert_non_full(Node* node, int key) {
        int i = (int)node->entries.size() - 1;
        if (node->is_leaf) {
            node->entries.push_back(Entry(0));
            while (i >= 0 && key < node->entries[i].key) {
                node->entries[i + 1] = node->entries[i];
                --i;
            }
            node->entries[i + 1] = Entry(key);
        } else {
            while (i >= 0 && key < node->entries[i].key) --i;
            ++i;
            if ((int)node->children[i]->entries.size() == MAX_KEYS) {
                split_child(node, i);
                if (key > node->entries[i].key) ++i;
            }
            insert_non_full(node->children[i], key);
        }
    }

    bool search_impl(Node* node, int key) const {
        if (!node) return false;
        int i = 0;
        while (i < (int)node->entries.size() && key > node->entries[i].key) ++i;
        if (i < (int)node->entries.size() && node->entries[i].key == key)
            return !node->entries[i].deleted;
        if (node->is_leaf) return false;
        return search_impl(node->children[i], key);
    }

    bool mark_deleted(Node* node, int key) {
        if (!node) return false;
        int i = 0;
        while (i < (int)node->entries.size() && key > node->entries[i].key) ++i;
        if (i < (int)node->entries.size() && node->entries[i].key == key) {
            if (node->entries[i].deleted) return false;
            node->entries[i].deleted = true;
            return true;
        }
        if (node->is_leaf) return false;
        return mark_deleted(node->children[i], key);
    }

    void collect_live(Node* node, std::vector<int>& keys) const {
        if (!node) return;
        for (int i = 0; i < (int)node->entries.size(); ++i) {
            if (!node->is_leaf && i < (int)node->children.size())
                collect_live(node->children[i], keys);
            if (!node->entries[i].deleted)
                keys.push_back(node->entries[i].key);
        }
        if (!node->is_leaf && !node->children.empty())
            collect_live(node->children.back(), keys);
    }

    void inorder_impl(Node* node, std::vector<int>& result) const {
        if (!node) return;
        for (int i = 0; i < (int)node->entries.size(); ++i) {
            if (!node->is_leaf && i < (int)node->children.size())
                inorder_impl(node->children[i], result);
            if (!node->entries[i].deleted)
                result.push_back(node->entries[i].key);
        }
        if (!node->is_leaf && !node->children.empty())
            inorder_impl(node->children.back(), result);
    }

    void count_active(Node* node, int& count) const {
        if (!node) return;
        for (auto& e : node->entries)
            if (!e.deleted) ++count;
        for (auto* c : node->children)
            count_active(c, count);
    }
};
