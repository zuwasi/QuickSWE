# Task 035: Constraint Solver for Scheduling

## Overview

Implement a constraint-based scheduler that assigns tasks to time slots and resources. Uses backtracking to find valid schedules that satisfy all constraints.

## Requirements

1. **Task model**: Each task has a name, duration (integer time units), and resource requirements (list of resource types needed).

2. **Resource model**: Each resource has a name, type, and availability windows (list of (start, end) tuples). A resource can only be used during its availability windows.

3. **Constraint types**:
   - `DependencyConstraint(before_task, after_task)` — `before_task` must finish before `after_task` starts.
   - `TimeWindowConstraint(task, earliest_start, latest_end)` — task must start >= earliest_start and end <= latest_end.
   - `ResourceConstraint(task, resource_type)` — task requires a resource of the given type.

4. **Scheduler**:
   - Takes a list of tasks, resources, and constraints.
   - Uses backtracking to find a valid schedule.
   - Returns a `Solution` object or `None` if no valid schedule exists.
   - Assignments: each task gets a start_time and assigned resources.
   - No resource double-booking: a resource assigned to one task for time [s, s+d) cannot be assigned to another task overlapping that interval.

5. **Solution**: Stores the assignment for each task (start_time, assigned resources). Can compute makespan (max end_time across all tasks).

6. **Best-effort optimization**: Among valid schedules, prefer lower makespan. (Doesn't need to be globally optimal — just better than random.)

## Existing Code

- `task_model.py` has a working Task class.
- `resource.py` has a working Resource class.
- Other files have stubs.

## Constraints

- Pure Python, no external solvers.
- Time is discrete integers (0, 1, 2, ...).
