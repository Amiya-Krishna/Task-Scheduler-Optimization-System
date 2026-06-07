"""
Task Scheduler Optimization System
====================================
src/models.py - Data models for tasks and resources

Author: Task Scheduler Project
DSA Concepts: Classes, Data Structures, OOP
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    """
    Represents a single schedulable task.
    
    DSA Role: Core node in dependency graph (DAG)
    """
    task_id: str
    task_name: str
    duration_h: int          # How long it takes (in hours)
    deadline_h: int          # Must finish by this hour
    priority: int            # 1 (lowest) to 5 (highest)
    skill: str               # Required skill type
    depends_on: List[str]    # List of task_ids that must finish first
    profit: int              # Value/score gained if completed on time

    # Computed fields
    start_h: Optional[int] = field(default=None)
    end_h: Optional[int] = field(default=None)
    assigned_resource: Optional[str] = field(default=None)
    is_completed: bool = field(default=False)
    lateness: int = field(default=0)

    def __post_init__(self):
        # Convert depends_on from string if needed
        if isinstance(self.depends_on, str):
            self.depends_on = [d for d in self.depends_on.split("|") if d]

    @property
    def slack(self) -> int:
        """Slack = deadline - duration. Lower slack = more urgent."""
        return self.deadline_h - self.duration_h

    @property
    def priority_score(self) -> float:
        """Combined score for scheduling decisions."""
        urgency = 1 / (self.slack + 1) if self.slack >= 0 else 999
        return (self.priority * 10) + (self.profit / 100) + urgency

    def __repr__(self):
        status = "✓" if self.is_completed else "✗"
        return (f"Task({self.task_id}, '{self.task_name}', prio={self.priority}, "
                f"ddl={self.deadline_h}h, dur={self.duration_h}h, {status})")


@dataclass
class Resource:
    """
    Represents a worker/machine that can execute tasks.
    
    DSA Role: Node in resource allocation graph
    """
    res_id: str
    res_name: str
    skills: set              # Set of skills this resource has
    shift_start_h: int       # When shift begins (e.g. 9 = 9AM)
    shift_end_h: int         # When shift ends (e.g. 17 = 5PM)
    max_hours_per_day: int
    hourly_cost: int

    # State tracking
    current_time: int = field(default=None)
    current_day: int = field(default=0)
    assigned_tasks: List[str] = field(default_factory=list)
    total_hours_worked: int = field(default=0)

    def __post_init__(self):
        if isinstance(self.skills, str):
            self.skills = set(self.skills.split("|"))
        if self.current_time is None:
            self.current_time = self.shift_start_h

    def can_handle(self, skill: str) -> bool:
        """Check if this resource has the required skill."""
        return skill in self.skills

    def available_from(self, min_start: int) -> int:
        """Returns the earliest available start time for this resource."""
        cur = max(self.current_time, min_start, self.shift_start_h + self.current_day * 24)
        while cur > self.shift_end_h + self.current_day * 24:
            self.current_day += 1
            cur = self.shift_start_h + self.current_day * 24
        return cur

    def __repr__(self):
        return f"Resource({self.res_id}, skills={self.skills}, {self.shift_start_h}-{self.shift_end_h}h)"


@dataclass
class ScheduleResult:
    """Final result container for a scheduled plan."""
    plan: list
    tasks: List[Task]
    resources: List[Resource]
    engine: str
    objective: str

    @property
    def on_time_count(self) -> int:
        return sum(1 for p in self.plan if p.get("lateness", 0) == 0)

    @property
    def on_time_pct(self) -> float:
        if not self.plan:
            return 0.0
        return round(100 * self.on_time_count / len(self.plan), 1)

    @property
    def total_lateness(self) -> int:
        return sum(p.get("lateness", 0) for p in self.plan)

    @property
    def total_profit(self) -> int:
        T = {t.task_id: t for t in self.tasks}
        return sum(T[p["task_id"]].profit for p in self.plan if p.get("lateness", 0) == 0)
