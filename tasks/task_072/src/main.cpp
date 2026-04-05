#include "scheduler.hpp"
#include <iostream>
#include <string>

void test_single_task() {
    Scheduler sched;
    sched.spawn([](Scheduler& s) -> std::vector<std::string> {
        return {"done"};
    });
    sched.run();
    bool ok = sched.is_completed(0);
    auto result = sched.join(0);
    ok = ok && result.has_value() && result.value().size() == 1 && result.value()[0] == "done";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_single_task" << std::endl;
}

void test_round_robin_order() {
    Scheduler sched;
    std::vector<int> exec_order;
    sched.spawn([&exec_order](Scheduler& s) -> std::vector<std::string> {
        exec_order.push_back(0);
        s.yield_task();
        exec_order.push_back(0);
        return {"a_done"};
    });
    sched.spawn([&exec_order](Scheduler& s) -> std::vector<std::string> {
        exec_order.push_back(1);
        s.yield_task();
        exec_order.push_back(1);
        return {"b_done"};
    });
    sched.run();
    // Expected: 0, 1, 0, 1 (round robin)
    bool ok = (exec_order.size() >= 4) &&
              exec_order[0] == 0 && exec_order[1] == 1 &&
              exec_order[2] == 0 && exec_order[3] == 1;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_round_robin_order" << std::endl;
}

void test_join_completed() {
    Scheduler sched;
    sched.spawn([](Scheduler& s) -> std::vector<std::string> {
        return {"result"};
    });
    sched.run();
    auto result = sched.join(0);
    bool ok = result.has_value() && result.value()[0] == "result";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_join_completed" << std::endl;
}

void test_yield_preserves_state() {
    Scheduler sched;
    sched.spawn([](Scheduler& s) -> std::vector<std::string> {
        int step = s.get_step(s.current());
        if (step == 0) {
            s.yield_task();
            return {};
        }
        return {"step_" + std::to_string(step)};
    });
    sched.run();
    auto result = sched.join(0);
    bool ok = result.has_value() && result.value().size() == 1 && result.value()[0] == "step_1";
    std::cout << (ok ? "PASS" : "FAIL") << ": test_yield_preserves_state" << std::endl;
}

void test_multiple_tasks_complete() {
    Scheduler sched;
    for (int i = 0; i < 5; ++i) {
        sched.spawn([i](Scheduler& s) -> std::vector<std::string> {
            return {"task_" + std::to_string(i)};
        });
    }
    sched.run();
    bool ok = true;
    for (int i = 0; i < 5; ++i)
        if (!sched.is_completed(i)) ok = false;
    std::cout << (ok ? "PASS" : "FAIL") << ": test_multiple_tasks_complete" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: " << argv[0] << " <test_name>\n"; return 1; }
    std::string test(argv[1]);
    if      (test == "test_single_task")             test_single_task();
    else if (test == "test_round_robin_order")       test_round_robin_order();
    else if (test == "test_join_completed")          test_join_completed();
    else if (test == "test_yield_preserves_state")   test_yield_preserves_state();
    else if (test == "test_multiple_tasks_complete") test_multiple_tasks_complete();
    else { std::cerr << "Unknown test: " << test << std::endl; return 1; }
    return 0;
}
