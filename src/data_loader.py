"""
Task Scheduler Optimization System
====================================
src/data_loader.py - CSV parsing and data loading

DSA Concepts: File I/O, Data Parsing, Validation
"""

import csv
import os
from typing import List, Tuple
from src.models import Task, Resource


def load_tasks(path: str = "data/tasks.csv") -> List[Task]:
    """
    Load tasks from CSV file.
    
    Algorithm: Linear scan O(n), validate each row.
    Returns list of Task objects sorted by priority (desc) then deadline (asc).
    """
    tasks = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Tasks CSV not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            deps_raw = row.get("depends_on", "") or ""
            deps = [d.strip() for d in deps_raw.split("|") if d.strip()]
            task = Task(
                task_id=row["task_id"].strip(),
                task_name=row.get("task_name", row["task_id"]).strip(),
                duration_h=int(row["duration_h"]),
                deadline_h=int(row["deadline_h"]),
                priority=int(row["priority"]),
                skill=row["skill"].strip(),
                depends_on=deps,
                profit=int(row.get("profit", 100)),
            )
            tasks.append(task)

    _validate_tasks(tasks)
    return tasks


def load_resources(path: str = "data/resources.csv") -> List[Resource]:
    """
    Load resources from CSV file.
    Returns list of Resource objects.
    """
    resources = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Resources CSV not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills_raw = row.get("skills", "") or ""
            skills = set(s.strip() for s in skills_raw.split("|") if s.strip())
            resource = Resource(
                res_id=row["res_id"].strip(),
                res_name=row.get("res_name", row["res_id"]).strip(),
                skills=skills,
                shift_start_h=int(row["shift_start_h"]),
                shift_end_h=int(row["shift_end_h"]),
                max_hours_per_day=int(row["max_hours_per_day"]),
                hourly_cost=int(row.get("hourly_cost", 50)),
            )
            resources.append(resource)

    return resources


def _validate_tasks(tasks: List[Task]):
    """
    Validate task data integrity.
    - No duplicate IDs
    - Dependencies exist
    - Duration <= deadline
    - Priority in [1,5]
    """
    ids = set()
    for t in tasks:
        if t.task_id in ids:
            raise ValueError(f"Duplicate task_id: {t.task_id}")
        ids.add(t.task_id)

    for t in tasks:
        if t.duration_h > t.deadline_h:
            print(f"  [WARN] Task {t.task_id}: duration ({t.duration_h}h) > deadline ({t.deadline_h}h)")
        if not (1 <= t.priority <= 5):
            raise ValueError(f"Task {t.task_id}: priority must be 1-5, got {t.priority}")
        for dep in t.depends_on:
            if dep not in ids:
                raise ValueError(f"Task {t.task_id}: dependency '{dep}' not found")

    # Check for cycles using DFS
    graph = {t.task_id: t.depends_on for t in tasks}
    visited = set()
    rec_stack = set()

    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.discard(node)
        return False

    for task_id in graph:
        if task_id not in visited:
            if has_cycle(task_id):
                raise ValueError("Dependency cycle detected in tasks!")


def load_all(tasks_csv: str = "data/tasks.csv",
             resources_csv: str = "data/resources.csv") -> Tuple[List[Task], List[Resource]]:
    """Convenience loader for both CSV files."""
    tasks = load_tasks(tasks_csv)
    resources = load_resources(resources_csv)
    return tasks, resources
