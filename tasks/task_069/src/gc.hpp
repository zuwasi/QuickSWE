#pragma once
#include <vector>
#include <set>
#include <map>
#include <algorithm>
#include <stdexcept>
#include <queue>

class GarbageCollector {
    struct Object {
        int id;
        int data;
        bool marked;
        int forwarding;  // new index after compaction, -1 if not set
        std::set<int> refs;  // IDs of referenced objects
        Object(int i, int d) : id(i), data(d), marked(false), forwarding(-1) {}
    };

public:
    GarbageCollector() : next_id_(0) {}

    int allocate(int data) {
        int id = next_id_++;
        objects_.emplace_back(id, data);
        id_to_idx_[id] = (int)objects_.size() - 1;
        return id;
    }

    void add_reference(int from_id, int to_id) {
        int idx = id_to_idx_.at(from_id);
        objects_[idx].refs.insert(to_id);
    }

    void set_root(int id) {
        roots_.insert(id);
    }

    void remove_root(int id) {
        roots_.erase(id);
    }

    int dereference(int id) const {
        int idx = id_to_idx_.at(id);
        return objects_[idx].data;
    }

    std::set<int> get_refs(int id) const {
        int idx = id_to_idx_.at(id);
        return objects_[idx].refs;
    }

    int live_count() const {
        int count = 0;
        for (const auto& obj : objects_) if (obj.marked) ++count;
        return count;
    }

    std::size_t heap_size() const { return objects_.size(); }

    void collect() {
        // Mark phase
        for (auto& obj : objects_) obj.marked = false;
        for (int root : roots_) {
            if (id_to_idx_.count(root)) {
                mark(id_to_idx_[root]);
            }
        }
        // Sweep: remove unmarked
        std::vector<Object> live;
        for (auto& obj : objects_) {
            if (obj.marked) live.push_back(obj);
        }
        objects_ = std::move(live);
        // Rebuild index
        id_to_idx_.clear();
        for (int i = 0; i < (int)objects_.size(); ++i) {
            id_to_idx_[objects_[i].id] = i;
        }
    }

    void compact() {
        // Compute forwarding addresses
        int write = 0;
        for (int i = 0; i < (int)objects_.size(); ++i) {
            objects_[i].forwarding = write++;
        }
        // Update references using forwarding pointers
        // (BUG: this loop doesn't actually update the refs)
        for (auto& obj : objects_) {
            std::set<int> new_refs;
            for (int ref_id : obj.refs) {
                new_refs.insert(ref_id);
            }
            obj.refs = new_refs;
        }
        // Move objects to new positions (already compact after collect)
    }

    std::vector<int> all_live_ids() const {
        std::vector<int> ids;
        for (const auto& obj : objects_) ids.push_back(obj.id);
        std::sort(ids.begin(), ids.end());
        return ids;
    }

private:
    std::vector<Object> objects_;
    std::map<int, int> id_to_idx_;
    std::set<int> roots_;
    int next_id_;

    void mark(int idx) {
        if (objects_[idx].marked) return;
        objects_[idx].marked = true;
        // BUG: doesn't recursively mark referenced objects
    }
};
