#pragma once
#include <functional>
#include <vector>
#include <algorithm>
#include <cmath>

enum class Color { RED, BLACK };

template <typename T>
class RBTree {
    struct Node {
        T key;
        Color color;
        Node* left;
        Node* right;
        Node* parent;
        Node(const T& k)
            : key(k), color(Color::RED), left(nullptr), right(nullptr), parent(nullptr) {}
    };

public:
    RBTree() : root_(nullptr), size_(0) {}

    ~RBTree() { destroy(root_); }

    void insert(const T& key) {
        Node* node = new Node(key);
        Node* parent = nullptr;
        Node* curr = root_;
        while (curr) {
            parent = curr;
            if (key < curr->key) curr = curr->left;
            else if (key > curr->key) curr = curr->right;
            else { delete node; return; }  // duplicate
        }
        node->parent = parent;
        if (!parent) root_ = node;
        else if (key < parent->key) parent->left = node;
        else parent->right = node;
        ++size_;
        fix_insert(node);
    }

    bool search(const T& key) const {
        Node* curr = root_;
        while (curr) {
            if (key < curr->key) curr = curr->left;
            else if (key > curr->key) curr = curr->right;
            else return true;
        }
        return false;
    }

    std::vector<T> inorder() const {
        std::vector<T> result;
        inorder_impl(root_, result);
        return result;
    }

    std::size_t size() const { return size_; }

    bool validate() const {
        if (!root_) return true;
        if (root_->color != Color::BLACK) return false;
        int black_count = -1;
        return validate_impl(root_, 0, black_count);
    }

    int height() const {
        return height_impl(root_);
    }

private:
    Node* root_;
    std::size_t size_;

    void destroy(Node* node) {
        if (!node) return;
        destroy(node->left);
        destroy(node->right);
        delete node;
    }

    void rotate_left(Node* x) {
        Node* y = x->right;
        x->right = y->left;
        if (y->left) y->left->parent = x;
        y->parent = x->parent;
        if (!x->parent) root_ = y;
        else if (x == x->parent->left) x->parent->left = y;
        else x->parent->right = y;
        y->left = x;
        x->parent = y;
    }

    void rotate_right(Node* x) {
        Node* y = x->left;
        x->left = y->right;
        if (y->right) y->right->parent = x;
        y->parent = x->parent;
        if (!x->parent) root_ = y;
        else if (x == x->parent->right) x->parent->right = y;
        else x->parent->left = y;
        y->right = x;
        x->parent = y;
    }

    void fix_insert(Node* z) {
        while (z->parent && z->parent->color == Color::RED) {
            if (z->parent == z->parent->parent->left) {
                Node* uncle = z->parent->parent->right;
                if (uncle && uncle->color == Color::BLACK) {
                    // Case 1: uncle is red — recolor
                    z->parent->color = Color::BLACK;
                    uncle->color = Color::BLACK;
                    z->parent->parent->color = Color::RED;
                    z = z->parent->parent;
                } else {
                    // Case 2/3: uncle is black — rotate
                    if (z == z->parent->right) {
                        z = z->parent;
                        rotate_left(z);
                    }
                    z->parent->color = Color::BLACK;
                    z->parent->parent->color = Color::RED;
                    rotate_right(z->parent->parent);
                }
            } else {
                Node* uncle = z->parent->parent->left;
                if (uncle && uncle->color == Color::BLACK) {
                    z->parent->color = Color::BLACK;
                    uncle->color = Color::BLACK;
                    z->parent->parent->color = Color::RED;
                    z = z->parent->parent;
                } else {
                    if (z == z->parent->left) {
                        z = z->parent;
                        rotate_right(z);
                    }
                    z->parent->color = Color::BLACK;
                    z->parent->parent->color = Color::RED;
                    rotate_left(z->parent->parent);
                }
            }
        }
        root_->color = Color::BLACK;
    }

    void inorder_impl(Node* node, std::vector<T>& result) const {
        if (!node) return;
        inorder_impl(node->left, result);
        result.push_back(node->key);
        inorder_impl(node->right, result);
    }

    bool validate_impl(Node* node, int blacks, int& expected) const {
        if (!node) {
            if (expected == -1) expected = blacks + 1;
            return blacks + 1 == expected;
        }
        if (node->color == Color::RED) {
            if ((node->left && node->left->color == Color::RED) ||
                (node->right && node->right->color == Color::RED))
                return false;
        }
        if (node->color == Color::BLACK) ++blacks;
        return validate_impl(node->left, blacks, expected) &&
               validate_impl(node->right, blacks, expected);
    }

    int height_impl(Node* node) const {
        if (!node) return 0;
        return 1 + std::max(height_impl(node->left), height_impl(node->right));
    }
};
