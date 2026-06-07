"""
Task Scheduler Optimization System
====================================
src/metrics.py - KPI Calculation & Performance Analytics

DSA Concepts: Aggregation, Hash Maps, Statistical Analysis
"""

from typing import List, Dict
from src.models import Task, Resource


def compute_kpis(plan: List[Dict], tasks: List[Task], resources: List[Resource]) -> Dict:
    """
    Compute all Key Performance Indicators for a schedule.
    
    Returns comprehensive metrics dict for reporting/UI.
    """
    task_map = {t.task_id: t for t in tasks}
    res_map = {r.res_id: r for r in resources}

    if not plan:
        return {}

    # ── Basic Counts ──────────────────────────────────────────────
    total_tasks = len(plan)
    scheduled = [p for p in plan if not p.get("missed", False)]
    missed = [p for p in plan if p.get("missed", False)]

    # ── Time Metrics ─────────────────────────────────────────────
    on_time = [p for p in scheduled if p.get("lateness", 0) == 0]
    late = [p for p in scheduled if p.get("lateness", 0) > 0]
    total_lateness = sum(p.get("lateness", 0) for p in scheduled)
    avg_lateness = total_lateness / len(scheduled) if scheduled else 0
    max_lateness = max((p.get("lateness", 0) for p in scheduled), default=0)

    # ── Profit / Score Metrics ────────────────────────────────────
    total_possible_profit = sum(t.profit for t in tasks)
    achieved_profit = sum(
        task_map[p["task_id"]].profit
        for p in on_time
        if p["task_id"] in task_map
    )
    profit_efficiency = round(100 * achieved_profit / total_possible_profit, 1) if total_possible_profit else 0

    # ── Resource Utilization ──────────────────────────────────────
    utilization: Dict[str, Dict] = {}
    for p in scheduled:
        rid = p.get("res_id")
        if not rid:
            continue
        if rid not in utilization:
            utilization[rid] = {
                "res_id": rid,
                "res_name": res_map[rid].res_name if rid in res_map else rid,
                "hours_worked": 0,
                "tasks_count": 0,
                "cost": 0,
            }
        hours = p.get("duration", 0)
        utilization[rid]["hours_worked"] += hours
        utilization[rid]["tasks_count"] += 1
        if rid in res_map:
            utilization[rid]["cost"] += hours * res_map[rid].hourly_cost

    # Calculate utilization %
    for rid, u in utilization.items():
        if rid in res_map:
            r = res_map[rid]
            max_hours = r.max_hours_per_day * 7  # weekly
            u["utilization_pct"] = round(100 * u["hours_worked"] / max_hours, 1) if max_hours else 0
        else:
            u["utilization_pct"] = 0

    # ── Makespan ─────────────────────────────────────────────────
    ends = [p["end"] for p in scheduled if p.get("end") is not None]
    makespan = max(ends) - min((p["start"] for p in scheduled if p.get("start") is not None), default=0) if ends else 0

    # ── Total Cost ────────────────────────────────────────────────
    total_cost = sum(u["cost"] for u in utilization.values())

    return {
        # Task metrics
        "total_tasks": total_tasks,
        "scheduled_tasks": len(scheduled),
        "missed_tasks": len(missed),
        "on_time_tasks": len(on_time),
        "late_tasks": len(late),
        "on_time_pct": round(100 * len(on_time) / total_tasks, 1),
        "schedule_success_pct": round(100 * len(scheduled) / total_tasks, 1),

        # Time metrics
        "total_lateness_h": total_lateness,
        "avg_lateness_h": round(avg_lateness, 2),
        "max_lateness_h": max_lateness,
        "makespan_h": makespan,

        # Profit metrics
        "total_possible_profit": total_possible_profit,
        "achieved_profit": achieved_profit,
        "profit_efficiency_pct": profit_efficiency,

        # Resource metrics
        "utilization": utilization,
        "total_cost": total_cost,

        # Detail lists
        "on_time_tasks_list": [p["task_id"] for p in on_time],
        "late_tasks_list": [{"task_id": p["task_id"], "lateness": p["lateness"]} for p in late],
        "missed_tasks_list": [p["task_id"] for p in missed],
    }


def compare_plans(plan_a: List[Dict], plan_b: List[Dict],
                  tasks: List[Task], resources: List[Resource],
                  label_a: str = "Greedy", label_b: str = "Optimized") -> Dict:
    """
    Compare two scheduling plans side-by-side.
    Returns delta metrics for dashboard comparison.
    """
    kpi_a = compute_kpis(plan_a, tasks, resources)
    kpi_b = compute_kpis(plan_b, tasks, resources)

    def delta(key):
        return round(kpi_b.get(key, 0) - kpi_a.get(key, 0), 2)

    return {
        label_a: kpi_a,
        label_b: kpi_b,
        "improvements": {
            "lateness_reduction_h": -delta("total_lateness_h"),
            "profit_gain": delta("achieved_profit"),
            "on_time_pct_gain": delta("on_time_pct"),
            "cost_change": delta("total_cost"),
        }
    }
