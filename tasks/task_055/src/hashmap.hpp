#pragma once
#include <vector>
#include <string>
#include <functional>
#include <utility>

template <typename K, typename V>
class HashMap {
    enum class SlotState { EMPTY, OCCUPIED, DELETED };

    struct Slot {
        K key{};
        V value{};
        SlotState state = SlotState::EMPTY;
    };

public:
    explicit HashMap(std::size_t capacity = 16)
        : table_(capacity), size_(0) {}

    void insert(const K& key, const V& value) {
        std::size_t idx = hash(key);
        for (std::size_t i = 0; i < table_.size(); ++i) {
            std::size_t pos = (idx + i) % table_.size();
            if (table_[pos].state == SlotState::EMPTY ||
                table_[pos].state == SlotState::DELETED) {
                table_[pos].key = key;
                table_[pos].value = value;
                table_[pos].state = SlotState::OCCUPIED;
                ++size_;
                return;
            }
            if (table_[pos].state == SlotState::OCCUPIED && table_[pos].key == key) {
                table_[pos].value = value;
                return;
            }
        }
    }

    std::pair<bool, V> get(const K& key) const {
        std::size_t idx = hash(key);
        for (std::size_t i = 0; i < table_.size(); ++i) {
            std::size_t pos = (idx + i) % table_.size();
            if (table_[pos].state == SlotState::EMPTY) return {false, V{}};
            if (table_[pos].state == SlotState::DELETED) return {false, V{}};
            if (table_[pos].key == key) return {true, table_[pos].value};
        }
        return {false, V{}};
    }

    bool remove(const K& key) {
        std::size_t idx = hash(key);
        for (std::size_t i = 0; i < table_.size(); ++i) {
            std::size_t pos = (idx + i) % table_.size();
            if (table_[pos].state == SlotState::EMPTY) return false;
            if (table_[pos].state == SlotState::OCCUPIED && table_[pos].key == key) {
                table_[pos].state = SlotState::DELETED;
                --size_;
                return true;
            }
        }
        return false;
    }

    bool contains(const K& key) const {
        return get(key).first;
    }

    std::size_t size() const { return size_; }

private:
    std::vector<Slot> table_;
    std::size_t size_;

    std::size_t hash(const K& key) const {
        return std::hash<K>{}(key) % table_.size();
    }
};
