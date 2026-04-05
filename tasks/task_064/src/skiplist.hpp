#pragma once
#include <vector>
#include <random>
#include <limits>
#include <optional>

template <typename T>
class SkipList {
    static constexpr int MAX_LEVEL = 16;

    struct Node {
        T key;
        std::vector<Node*> forward;
        Node(const T& k, int level) : key(k), forward(level + 1, nullptr) {}
    };

public:
    explicit SkipList(unsigned seed = 42)
        : level_(0), size_(0), gen_(seed), dist_(0.0, 1.0) {
        head_ = new Node(T{}, MAX_LEVEL);
    }

    ~SkipList() {
        Node* curr = head_;
        while (curr) {
            Node* next = curr->forward[0];
            delete curr;
            curr = next;
        }
    }

    void insert(const T& key) {
        std::vector<Node*> update(MAX_LEVEL + 1, nullptr);
        Node* curr = head_;
        for (int i = level_; i >= 0; --i) {
            while (curr->forward[i] && curr->forward[i]->key < key)
                curr = curr->forward[i];
            update[i] = curr;
        }
        curr = curr->forward[0];
        if (curr && curr->key == key) return;

        int new_level = random_level();
        if (new_level > level_) {
            for (int i = level_ + 1; i <= new_level; ++i)
                update[i] = head_;
            level_ = new_level;
        }

        Node* node = new Node(key, new_level);
        for (int i = 0; i <= new_level; ++i) {
            node->forward[i] = update[i]->forward[i];
        }
        for (int i = 0; i <= 0; ++i) {
            update[i]->forward[i] = node;
        }
        ++size_;
    }

    bool search(const T& key) const {
        Node* curr = head_;
        for (int i = level_; i >= 0; --i) {
            while (curr->forward[i] && curr->forward[i]->key < key)
                curr = curr->forward[i];
        }
        curr = curr->forward[0];
        return curr && curr->key == key;
    }

    bool remove(const T& key) {
        std::vector<Node*> update(MAX_LEVEL + 1, nullptr);
        Node* curr = head_;
        for (int i = level_; i >= 0; --i) {
            while (curr->forward[i] && curr->forward[i]->key < key)
                curr = curr->forward[i];
            update[i] = curr;
        }
        curr = curr->forward[0];
        if (!curr || curr->key != key) return false;

        for (int i = 0; i <= level_; ++i) {
            if (update[i]->forward[i] != curr) break;
            update[i]->forward[i] = curr->forward[i];
        }
        delete curr;
        --size_;
        return true;
    }

    std::size_t size() const { return size_; }

    std::vector<T> to_vector() const {
        std::vector<T> result;
        Node* curr = head_->forward[0];
        while (curr) {
            result.push_back(curr->key);
            curr = curr->forward[0];
        }
        return result;
    }

    int current_level() const { return level_; }

private:
    Node* head_;
    int level_;
    std::size_t size_;
    mutable std::mt19937 gen_;
    mutable std::uniform_real_distribution<double> dist_;

    int random_level() {
        int lvl = 0;
        while (dist_(gen_) < 0.5 && lvl < MAX_LEVEL)
            ++lvl;
        return lvl;
    }
};
