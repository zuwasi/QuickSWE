#ifndef SKIPLIST_H
#define SKIPLIST_H

#include <cstdlib>
#include <ctime>
#include <iostream>

template<typename T>
class SkipList {
public:
    struct Node {
        T value;
        Node** forward;
        int level;

        Node(const T& val, int lvl)
            : value(val), level(lvl) {
            forward = new Node*[lvl + 1];
            for (int i = 0; i <= lvl; i++) forward[i] = nullptr;
        }

        ~Node() { delete[] forward; }
    };

private:
    static const int MAX_LEVEL = 8;
    Node* head_;
    int level_;
    int size_;

    int randomLevel() {
        int lvl = 0;
        while (lvl < MAX_LEVEL && (rand() % 2) == 0) lvl++;
        return lvl;
    }

public:
    SkipList() : level_(0), size_(0) {
        srand((unsigned)time(nullptr));
        head_ = new Node(T(), MAX_LEVEL);
    }

    ~SkipList() {
        Node* cur = head_->forward[0];
        while (cur) {
            Node* next = cur->forward[0];
            delete cur;
            cur = next;
        }
        delete head_;
    }

    void insert(const T& value) {
        Node* update[MAX_LEVEL + 1];
        Node* cur = head_;

        for (int i = level_; i >= 0; i--) {
            while (cur->forward[i] && cur->forward[i]->value < value)
                cur = cur->forward[i];
            update[i] = cur;
        }

        cur = cur->forward[0];
        if (cur && cur->value == value) return;  /* duplicate */

        int newLevel = randomLevel();
        if (newLevel > level_) {
            for (int i = level_ + 1; i <= newLevel; i++)
                update[i] = head_;
            level_ = newLevel;
        }

        Node* newNode = new Node(value, newLevel);
        for (int i = 0; i <= newLevel; i++) {
            newNode->forward[i] = update[i]->forward[i];
            update[i]->forward[i] = newNode;
        }
        size_++;
    }

    bool contains(const T& value) const {
        Node* cur = head_;
        for (int i = level_; i >= 0; i--) {
            while (cur->forward[i] && cur->forward[i]->value < value)
                cur = cur->forward[i];
        }
        cur = cur->forward[0];
        return cur && cur->value == value;
    }

    bool remove(const T& value) {
        Node* update[MAX_LEVEL + 1];
        Node* cur = head_;

        for (int i = level_; i >= 0; i--) {
            while (cur->forward[i] && cur->forward[i]->value < value)
                cur = cur->forward[i];
            update[i] = cur;
        }

        cur = cur->forward[0];
        if (!cur || cur->value != value) return false;

        for (int i = 0; i <= level_; i++) {
            if (update[i]->forward[i] != cur) break;
            update[i]->forward[i] = cur->forward[i];
        }

        delete cur;
        while (level_ > 0 && !head_->forward[level_]) level_--;
        size_--;
        return true;
    }

    int size() const { return size_; }
    bool empty() const { return size_ == 0; }

    /* TODO: Add iterator class here */
    /* TODO: Add begin(), end(), cbegin(), cend() */

    void print() const {
        Node* cur = head_->forward[0];
        while (cur) {
            std::cout << cur->value;
            if (cur->forward[0]) std::cout << " ";
            cur = cur->forward[0];
        }
        std::cout << std::endl;
    }
};

#endif
