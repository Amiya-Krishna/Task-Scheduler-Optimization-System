"""
Task Scheduler Optimization System
====================================
src/report_generator.py - Schedule Report Generation (CSV + Text)

DSA Concepts: Formatting, File I/O, Data Aggregation
"""

import csv
import os
import json
from datetime import datetime
from typing import List, Dict


def generate_text_report(plan: List[Dict], kpis: Dict, engine: str = "Greedy") -> str:
    """
    Generate a human-readable schedule report.
    Returns formatted string report.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    lines.append("=" * 70)
    lines.append("       TASK SCHEDULER OPTIMIZATION SYSTEM — SCHEDULE REPORT")
    lines.append("=" * 70)
    lines.append(f"  Generated: {ts}")
    lines.append(f"  Engine   : {engine.upper()}")
    lines.append("=" * 70)

    lines.append("\n📊 KEY PERFORMANCE INDICATORS")
    lines.append("-" * 40)
    lines.append(f"  Total Tasks       : {kpis.get('total_tasks', 0)}")
    lines.append(f"  Scheduled         : {kpis.get('scheduled_tasks', 0)}")
    lines.append(f"  On-Time           : {kpis.get('on_time_tasks', 0)}  ({kpis.get('on_time_pct', 0)}%)")
    lines.append(f"  Late              : {kpis.get('late_tasks', 0)}")
    lines.append(f"  Missed/Failed     : {kpis.get('missed_tasks', 0)}")
    lines.append(f"  Total Lateness    : {kpis.get('total_lateness_h', 0)} hours")
    lines.append(f"  Makespan          : {kpis.get('makespan_h', 0)} hours")
    lines.append(f"  Achieved Profit   : {kpis.get('achieved_profit', 0)} / {kpis.get('total_possible_profit', 0)}")
    lines.append(f"  Profit Efficiency : {kpis.get('profit_efficiency_pct', 0)}%")
    lines.append(f"  Total Cost        : ${kpis.get('total_cost', 0)}")

    lines.append("\n📅 OPTIMIZED SCHEDULE TIMELINE")
    lines.append("-" * 70)
    lines.append(f"  {'TASK ID':<8} {'TASK NAME':<25} {'RESOURCE':<18} {'START':>6} {'END':>6} {'LATE':>5} {'STATUS'}")
    lines.append("  " + "-" * 67)

    for p in sorted(plan, key=lambda x: (x.get("start") or 999, x["task_id"])):
        missed = p.get("missed", False)
        start = f"{p['start']}h" if p.get("start") is not None else "N/A"
        end = f"{p['end']}h" if p.get("end") is not None else "N/A"
        lateness = p.get("lateness", 0)
        status = "MISSED ✗" if missed else ("ON TIME ✓" if lateness == 0 else f"LATE({lateness}h) ⚠")
        resource = p.get("res_name", p.get("res_id", "N/A"))

        lines.append(
            f"  {p['task_id']:<8} {p['task_name'][:24]:<25} {resource[:17]:<18} "
            f"{start:>6} {end:>6} {lateness:>5} {status}"
        )

    lines.append("\n⚡ RESOURCE UTILIZATION")
    lines.append("-" * 40)
    for rid, u in kpis.get("utilization", {}).items():
        lines.append(
            f"  {u['res_name'][:20]:<22}: {u['hours_worked']}h worked, "
            f"{u['tasks_count']} tasks, {u.get('utilization_pct', 0)}% util, "
            f"${u.get('cost', 0)} cost"
        )

    if kpis.get("missed_tasks_list"):
        lines.append("\n❌ MISSED TASKS (Could not be scheduled)")
        lines.append("-" * 40)
        for tid in kpis["missed_tasks_list"]:
            lines.append(f"  • {tid}")

    lines.append("\n" + "=" * 70)
    lines.append("  END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


def save_text_report(report: str, output_path: str = "outputs/schedule_report.txt"):
    """Save text report to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  ✓ Text report saved: {output_path}")


def save_csv_report(plan: List[Dict], output_path: str = "outputs/schedule_output.csv"):
    """Save plan as CSV for spreadsheet analysis."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not plan:
        return
    fieldnames = ["task_id", "task_name", "res_id", "res_name",
                  "start", "end", "duration", "deadline", "priority",
                  "skill", "profit", "lateness", "missed"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(plan, key=lambda x: (x.get("start") or 999, x["task_id"])):
            writer.writerow(row)
    print(f"  ✓ CSV report saved: {output_path}")


def save_json_report(data: Dict, output_path: str = "outputs/schedule_data.json"):
    """Save full schedule data as JSON for dashboard/API."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ JSON data saved: {output_path}")
