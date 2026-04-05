#pragma once
#include <functional>
#include <vector>
#include <queue>
#include <map>
#include <string>
#include <optional>

class Scheduler {
public:
    using TaskFn = std::function<std::vector<std::string>(Scheduler&)>;

    enum class TaskState { READY, RUNNING, YIELDED, COMPLETED };

    struct Task {
        int id;
        TaskFn fn;
        TaskState state;
        std::vector<std::string> result;
        int step;  // execution step for simulation
        Task(int i, TaskFn f) : id(i), fn(f), state(TaskState::READY), step(0) {}
    };

    int spawn(TaskFn fn) {
        int id = next_id_++;
        tasks_[id] = Task(id, fn);
        ready_queue_.push(id);
        return id;
    }

    void run() {
        while (!ready_queue_.empty()) {
            int id = ready_queue_.front();
            ready_queue_.pop();
            if (tasks_.find(id) == tasks_.end()) continue;
            auto& task = tasks_[id];
            if (task.state == TaskState::COMPLETED) continue;

            task.state = TaskState::RUNNING;
            current_task_ = id;
            yielded_ = false;
            task.result = task.fn(*this);

            if (!yielded_) {
                task.state = TaskState::COMPLETED;
            }
        }
    }

    void yield_task() {
        yielded_ = true;
        auto& task = tasks_[current_task_];
        task.state = TaskState::YIELDED;
        task.step++;
        // Re-enqueue — but at front instead of back (bug)
        std::queue<int> new_q;
        new_q.push(current_task_);
        while (!ready_queue_.empty()) {
            new_q.push(ready_queue_.front());
            ready_queue_.pop();
        }
        ready_queue_ = new_q;
    }

    bool is_completed(int id) const {
        auto it = tasks_.find(id);
        if (it == tasks_.end()) return false;
        return it->second.state == TaskState::COMPLETED;
    }

    std::optional<std::vector<std::string>> join(int id) {
        auto it = tasks_.find(id);
        if (it == tasks_.end()) return std::nullopt;
        if (it->second.state != TaskState::COMPLETED) return std::nullopt;
        return it->second.result;
    }

    int get_step(int id) const {
        auto it = tasks_.find(id);
        return it != tasks_.end() ? it->second.step : -1;
    }

    int current() const { return current_task_; }

    std::size_t pending_count() const { return ready_queue_.size(); }

private:
    std::map<int, Task> tasks_;
    std::queue<int> ready_queue_;
    int next_id_ = 0;
    int current_task_ = -1;
    bool yielded_ = false;
};
