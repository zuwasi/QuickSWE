#ifndef BST_HPP
#define BST_HPP

#include <vector>
#include <functional>
#include <sstream>
#include <string>

template <typename T>
class BST {
private:
    struct Node {
        T value;
        Node *left;
        Node *right;
        Node(const T &val) : value(val), left(nullptr), right(nullptr) {}
    };

    Node *root;
    int node_count;

    Node *insert_helper(Node *node, const T &value) {
        if (!node) {
            node_count++;
            return new Node(value);
        }
        if (value < node->value) {
            node->left = insert_helper(node->left, value);
        } else if (value > node->value) {
            node->right = insert_helper(node->right, value);
        }
        /* duplicates ignored */
        return node;
    }

    Node *find_min(Node *node) {
        while (node && node->left) {
            node = node->left;
        }
        return node;
    }

    Node *remove_helper(Node *node, const T &value) {
        if (!node) return nullptr;

        if (value < node->value) {
            node->left = remove_helper(node->left, value);
        } else if (value > node->value) {
            node->right = remove_helper(node->right, value);
        } else {
            /* Found the node to delete */
            if (!node->left && !node->right) {
                /* Leaf node */
                delete node;
                node_count--;
                return nullptr;
            } else if (!node->left) {
                /* Only right child */
                Node *right = node->right;
                delete node;
                node_count--;
                return right;
            } else if (!node->right) {
                /* Only left child */
                Node *left = node->left;
                delete node;
                node_count--;
                return left;
            } else {
                /*
                 * Two children: find in-order successor (min of right subtree)
                 * Copy its value, then delete the successor.
                 *
                 * BUG: We find the successor and copy its value, but then we
                 * try to delete the successor by searching for it in the right
                 * subtree. However, our remove_helper for the successor node
                 * doesn't properly handle the case where the successor has a
                 * right child that needs to be relinked to the successor's parent.
                 *
                 * Actually, the real bug is more subtle: we manually unlink the
                 * successor below instead of using the recursive remove, and we
                 * forget to relink the successor's right child.
                 */
                Node *successor = find_min(node->right);
                node->value = successor->value;

                /* BUG: Manual unlinking that drops successor's right subtree.
                 * We walk down to find the successor and just set the parent's
                 * left pointer to NULL, discarding any right child the successor had.
                 *
                 * Correct approach: node->right = remove_helper(node->right, successor->value);
                 */
                if (node->right == successor) {
                    /* Successor is immediate right child */
                    node->right = nullptr;  /* BUG: drops successor->right! */
                    delete successor;
                    node_count--;
                } else {
                    /* Walk to find successor's parent */
                    Node *parent = node->right;
                    while (parent->left != successor) {
                        parent = parent->left;
                    }
                    parent->left = nullptr;  /* BUG: drops successor->right! */
                    delete successor;
                    node_count--;
                }
            }
        }
        return node;
    }

    bool find_helper(Node *node, const T &value) const {
        if (!node) return false;
        if (value < node->value) return find_helper(node->left, value);
        if (value > node->value) return find_helper(node->right, value);
        return true;
    }

    void inorder_helper(Node *node, std::vector<T> &result) const {
        if (!node) return;
        inorder_helper(node->left, result);
        result.push_back(node->value);
        inorder_helper(node->right, result);
    }

    int height_helper(Node *node) const {
        if (!node) return 0;
        int lh = height_helper(node->left);
        int rh = height_helper(node->right);
        return 1 + (lh > rh ? lh : rh);
    }

    void destroy_helper(Node *node) {
        if (!node) return;
        destroy_helper(node->left);
        destroy_helper(node->right);
        delete node;
    }

    bool is_bst_helper(Node *node, const T *min, const T *max) const {
        if (!node) return true;
        if (min && node->value <= *min) return false;
        if (max && node->value >= *max) return false;
        return is_bst_helper(node->left, min, &node->value) &&
               is_bst_helper(node->right, &node->value, max);
    }

public:
    BST() : root(nullptr), node_count(0) {}

    ~BST() {
        destroy_helper(root);
    }

    void insert(const T &value) {
        root = insert_helper(root, value);
    }

    void remove(const T &value) {
        root = remove_helper(root, value);
    }

    bool find(const T &value) const {
        return find_helper(root, value);
    }

    std::vector<T> inorder() const {
        std::vector<T> result;
        inorder_helper(root, result);
        return result;
    }

    int height() const {
        return height_helper(root);
    }

    int size() const {
        return node_count;
    }

    bool is_valid_bst() const {
        return is_bst_helper(root, nullptr, nullptr);
    }

    std::string inorder_string() const {
        std::vector<T> values = inorder();
        std::ostringstream oss;
        for (size_t i = 0; i < values.size(); i++) {
            if (i > 0) oss << " ";
            oss << values[i];
        }
        return oss.str();
    }
};

#endif /* BST_HPP */
