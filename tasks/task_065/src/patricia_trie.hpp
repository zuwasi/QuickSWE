#pragma once
#include <string>
#include <unordered_map>
#include <vector>
#include <algorithm>

class PatriciaTrie {
    struct Node {
        std::string edge_label;
        bool is_end;
        std::unordered_map<char, Node*> children;
        Node() : is_end(false) {}
        ~Node() { for (auto& [k, v] : children) delete v; }
    };

public:
    PatriciaTrie() : root_(new Node()), size_(0) {}
    ~PatriciaTrie() { delete root_; }

    void insert(const std::string& key) {
        if (key.empty()) { root_->is_end = true; ++size_; return; }
        insert_impl(root_, key, 0);
    }

    bool search(const std::string& key) const {
        if (key.empty()) return root_->is_end;
        return search_impl(root_, key, 0);
    }

    bool starts_with(const std::string& prefix) const {
        if (prefix.empty()) return true;
        return starts_with_impl(root_, prefix, 0);
    }

    std::vector<std::string> all_keys() const {
        std::vector<std::string> result;
        collect(root_, "", result);
        std::sort(result.begin(), result.end());
        return result;
    }

    std::size_t size() const { return size_; }

private:
    Node* root_;
    std::size_t size_;

    void insert_impl(Node* node, const std::string& key, std::size_t depth) {
        char first = key[depth];
        auto it = node->children.find(first);
        if (it == node->children.end()) {
            Node* leaf = new Node();
            leaf->edge_label = key.substr(depth);
            leaf->is_end = true;
            node->children[first] = leaf;
            ++size_;
            return;
        }

        Node* child = it->second;
        const std::string& edge = child->edge_label;
        std::size_t match_len = 0;
        while (match_len < edge.size() && depth + match_len < key.size() &&
               edge[match_len] == key[depth + match_len]) {
            ++match_len;
        }

        if (match_len == edge.size()) {
            if (depth + match_len == key.size()) {
                if (!child->is_end) { child->is_end = true; ++size_; }
                return;
            }
            insert_impl(child, key, depth + match_len);
            return;
        }

        // Need to split
        Node* split = new Node();
        split->edge_label = edge.substr(0, match_len);
        node->children[first] = split;

        child->edge_label = edge.substr(match_len);
        split->children[child->edge_label[0]] = child;

        if (depth + match_len == key.size()) {
            split->is_end = true;
            ++size_;
        } else {
            Node* new_leaf = new Node();
            new_leaf->edge_label = key.substr(depth + match_len + 1);
            new_leaf->is_end = true;
            split->children[key[depth + match_len]] = new_leaf;
            ++size_;
        }
    }

    bool search_impl(Node* node, const std::string& key, std::size_t depth) const {
        char first = key[depth];
        auto it = node->children.find(first);
        if (it == node->children.end()) return false;

        Node* child = it->second;
        const std::string& edge = child->edge_label;
        std::size_t remaining = key.size() - depth;
        if (remaining < edge.size()) return false;
        if (key.compare(depth, edge.size(), edge) != 0) return false;

        if (depth + edge.size() == key.size()) return child->is_end;
        return search_impl(child, key, depth + edge.size());
    }

    bool starts_with_impl(Node* node, const std::string& prefix, std::size_t depth) const {
        char first = prefix[depth];
        auto it = node->children.find(first);
        if (it == node->children.end()) return false;

        Node* child = it->second;
        const std::string& edge = child->edge_label;
        std::size_t remaining = prefix.size() - depth;

        if (remaining <= edge.size()) {
            return prefix.compare(depth, remaining, edge, 0, remaining) == 0;
        }
        if (prefix.compare(depth, edge.size(), edge) != 0) return false;
        return starts_with_impl(child, prefix, depth + edge.size());
    }

    void collect(Node* node, const std::string& prefix, std::vector<std::string>& result) const {
        std::string current = prefix + node->edge_label;
        if (node->is_end) result.push_back(current);
        for (auto& [ch, child] : node->children) {
            collect(child, current, result);
        }
    }
};
