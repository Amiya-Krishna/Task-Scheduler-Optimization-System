"""
Task Scheduler Optimization System
====================================
src/greedy_scheduler.py - Greedy Scheduling Algorithm

DSA Concepts Used:
  - Topological Sort (Kahn's Algorithm with BFS)
  - Max-Heap / Priority Queue (heapq)
  - Greedy Algorithm (EDF + Priority hybrid)
  - Adjacency List (dependency graph)
  - Hash Maps (lookup tables)

Time Complexity:  O(n log n) for sorting + O(V+E) for topological sort
Space Complexity: O(n) for queue and state tracking
"""

import heapq
from collections import defaultdict, deque
from copy import deepcopy
from typing import List, Dict, Optional

from src.models import Task, Resource


def topological_sort(tasks: List[Task]) -> List[str]:
    """
    Kahn's Algorithm (BFS-based topological sort) with priority tie-breaking.
    
    DSA: This is BFS on a DAG (Directed Acyclic Graph).
    Time: O(V + E) where V = tasks, E = dependencies
    
    Returns task_ids in valid execution order.
    """
    # Build adjacency list and in-degree map
    # In-degree: how many dependencies a task has
    in_degree = defaultdict(int)
    children = defaultdict(list)      # who depends on whom (adjacency list)
    lookup: Dict[str, Task] = {t.task_id: t for t in tasks}

    for t in tasks:
        if t.task_id not in in_degree:
            in_degree[t.task_id] = 0
        for dep in t.depends_on:
            in_degree[t.task_id] += 1
            children[dep].append(t.task_id)

    # Initialize priority queue with tasks that have no dependencies
    # Max-heap: use negative priority for max behavior in Python's min-heap
    # Tie-break: higher priority first, then earlier deadline
    # Heap element: (-priority, deadline, task_id)
    ready_heap = []
    for t in tasks:
        if in_degree[t.task_id] == 0:
            heapq.heappush(ready_heap, (-t.priority, t.deadline_h, t.task_id))

    topo_order = []

    while ready_heap:
        # Pop highest priority task (greedy choice)
        neg_prio, ddl, tid = heapq.heappop(ready_heap)
        topo_order.append(tid)

        # Reduce in-degree of children; add to heap if ready
        for child_id in children[tid]:
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0:
                child = lookup[child_id]
                heapq.heappush(ready_heap, (-child.priority, child.deadline_h, child_id))

    if len(topo_order) != len(tasks):
        raise RuntimeError("Cycle detected — cannot produce topological order!")

    return topo_order


def greedy_schedule(tasks: List[Task], resources: List[Resource], horizon: int = 168) -> List[Dict]:
    """
    Greedy Scheduler: assigns tasks to resources using priority + EDF heuristic.
    
    Strategy:
      1. Topological sort respecting dependencies
      2. For each task, find the best resource (earliest feasible slot, min lateness)
      3. Track resource availability using per-resource time cursors
    
    DSA: Priority Queue + Greedy + Topological Sort
    Time: O(n * r) where n=tasks, r=resources
    """
    lookup: Dict[str, Task] = {t.task_id: deepcopy(t) for t in tasks}
    
    # Reset resource state (important for re-runs)
    res_list = [deepcopy(r) for r in resources]
    res_map: Dict[str, Resource] = {r.res_id: r for r in res_list}

    # Track earliest end time for each task (for dependency handling)
    earliest_end: Dict[str, int] = {}

    topo_order = topological_sort(tasks)
    plan = []

    for tid in topo_order:
        task = lookup[tid]

        # Constraint: can't start until all dependencies are done
        dep_end = max((earliest_end.get(dep, 0) for dep in task.depends_on), default=0)

        best_assignment = None
        best_score = float("inf")

        # Try each compatible resource (greedy: pick best one)
        for res in res_list:
            if not res.can_handle(task.skill):
                continue

            # Earliest possible start for this resource
            # = max(resource free time, dependency end, shift start)
            day = res.current_day
            cur = max(res.current_time, dep_end)

            # Advance to next valid shift window if needed
            max_days = horizon // 24 + 2
            placed = False
            for _ in range(max_days):
                shift_start = res.shift_start_h + day * 24
                shift_end = res.shift_end_h + day * 24

                # Task must fit within this day's shift
                earliest = max(cur, shift_start)
                if earliest + task.duration_h <= shift_end and earliest + task.duration_h <= horizon:
                    start_time = earliest
                    end_time = start_time + task.duration_h
                    lateness = max(0, end_time - task.deadline_h)

                    # Score: lower is better
                    # Weights: lateness heavily penalized, priority rewards early assignment
                    score = (lateness * 100) - (task.priority * 20) - (task.profit * 0.1)

                    if score < best_score:
                        best_score = score
                        best_assignment = {
                            "task_id": tid,
                            "task_name": task.task_name,
                            "res_id": res.res_id,
                            "res_name": res.res_name,
                            "start": start_time,
                            "end": end_time,
                            "duration": task.duration_h,
                            "deadline": task.deadline_h,
                            "priority": task.priority,
                            "skill": task.skill,
                            "profit": task.profit,
                            "lateness": lateness,
                        }
                    placed = True
                    break
                else:
                    day += 1
                    cur = res.shift_start_h + day * 24

            if not placed and not best_assignment:
                continue

        if best_assignment is None:
            # Task cannot be scheduled — mark as missed
            plan.append({
                "task_id": tid,
                "task_name": task.task_name,
                "res_id": None,
                "res_name": "UNASSIGNED",
                "start": None,
                "end": None,
                "duration": task.duration_h,
                "deadline": task.deadline_h,
                "priority": task.priority,
                "skill": task.skill,
                "profit": task.profit,
                "lateness": task.deadline_h,  # Maximum lateness
                "missed": True,
            })
            earliest_end[tid] = task.deadline_h + task.duration_h
        else:
            # Update resource state
            res = res_map[best_assignment["res_id"]]
            res.current_time = best_assignment["end"]
            res.total_hours_worked += task.duration_h
            res.assigned_tasks.append(tid)

            best_assignment["missed"] = False
            plan.append(best_assignment)
            earliest_end[tid] = best_assignment["end"]

    return plan
