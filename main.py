"""
Task Scheduler Optimization System
====================================
main.py — Main CLI Entry Point

Run: python main.py [--engine greedy] [--horizon 72] [--report]

DSA Concepts Demonstrated:
  - Topological Sort (Kahn's Algorithm)
  - Priority Queue / Max-Heap (heapq)
  - Greedy Algorithm
  - Dependency Graph (DAG)
  - Hash Maps / Dictionaries
  - Sorting (multi-key)
"""

import argparse
import json
import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_all
from src.greedy_scheduler import greedy_schedule
from src.metrics import compute_kpis
from src.report_generator import (
    generate_text_report,
    save_text_report,
    save_csv_report,
    save_json_report,
)


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║        TASK SCHEDULER OPTIMIZATION SYSTEM  v1.0             ║
║        DSA Course Project  |  GitHub: @your-username        ║
╠══════════════════════════════════════════════════════════════╣
║  Algorithms: Greedy + Priority Queue + Topological Sort     ║
║  Language  : Python 3.10+  |  No heavy dependencies        ║
╚══════════════════════════════════════════════════════════════╝
"""


def run_scheduler(
    tasks_csv: str = "data/tasks.csv",
    resources_csv: str = "data/resources.csv",
    engine: str = "greedy",
    horizon: int = 168,
    save_report: bool = True,
    verbose: bool = True,
) -> dict:
    """
    Full pipeline:
    1. Load data  →  2. Schedule  →  3. Compute KPIs  →  4. Report
    """

    if verbose:
        print(BANNER)

    # ── Step 1: Load ─────────────────────────────────────────────
    print("━" * 60)
    print("  [1/4] Loading tasks and resources...")
    tasks, resources = load_all(tasks_csv, resources_csv)
    print(f"  ✓ Loaded {len(tasks)} tasks, {len(resources)} resources")

    # ── Step 2: Schedule ─────────────────────────────────────────
    print("\n  [2/4] Running scheduling algorithm...")
    t0 = time.perf_counter()

    if engine == "greedy":
        plan = greedy_schedule(tasks, resources, horizon=horizon)
    else:
        print(f"  [WARN] Engine '{engine}' not implemented. Using greedy.")
        plan = greedy_schedule(tasks, resources, horizon=horizon)

    elapsed = time.perf_counter() - t0
    print(f"  ✓ Schedule computed in {elapsed*1000:.2f}ms")

    # ── Step 3: KPIs ─────────────────────────────────────────────
    print("\n  [3/4] Computing KPIs...")
    kpis = compute_kpis(plan, tasks, resources)

    # Quick summary
    print(f"\n  {'═'*55}")
    print(f"  📊 RESULTS SUMMARY")
    print(f"  {'═'*55}")
    print(f"  On-time rate     : {kpis['on_time_pct']}%  ({kpis['on_time_tasks']}/{kpis['total_tasks']} tasks)")
    print(f"  Total lateness   : {kpis['total_lateness_h']}h")
    print(f"  Achieved profit  : {kpis['achieved_profit']} / {kpis['total_possible_profit']}")
    print(f"  Profit efficiency: {kpis['profit_efficiency_pct']}%")
    print(f"  Makespan         : {kpis['makespan_h']}h")
    print(f"  Total cost       : ${kpis['total_cost']}")

    # Show schedule table
    print(f"\n  📅 OPTIMIZED SCHEDULE")
    print(f"  {'─'*65}")
    print(f"  {'ID':<6} {'Task Name':<22} {'Resource':<18} {'Start':>5} {'End':>5} {'Status'}")
    print(f"  {'─'*65}")
    for p in sorted(plan, key=lambda x: (x.get("start") or 999, x["task_id"])):
        missed = p.get("missed", False)
        s = f"{p['start']}h" if p.get("start") is not None else "N/A"
        e = f"{p['end']}h" if p.get("end") is not None else "N/A"
        late = p.get("lateness", 0)
        status = "MISSED ✗" if missed else ("✓ ON TIME" if late == 0 else f"⚠ LATE {late}h")
        res = p.get("res_name", p.get("res_id", "—"))[:17]
        print(f"  {p['task_id']:<6} {p['task_name'][:21]:<22} {res:<18} {s:>5} {e:>5}  {status}")

    # Resource utilization
    print(f"\n  ⚡ RESOURCE UTILIZATION")
    print(f"  {'─'*50}")
    for rid, u in kpis["utilization"].items():
        bar_len = int(u.get("utilization_pct", 0) / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {u['res_name'][:18]:<20} [{bar}] {u.get('utilization_pct', 0):>5.1f}%  {u['hours_worked']}h")

    # ── Step 4: Save Reports ──────────────────────────────────────
    if save_report:
        print(f"\n  [4/4] Saving reports...")
        report_text = generate_text_report(plan, kpis, engine)
        save_text_report(report_text, "outputs/schedule_report.txt")
        save_csv_report(plan, "outputs/schedule_output.csv")
        save_json_report({"plan": plan, "kpis": kpis}, "outputs/schedule_data.json")

    print(f"\n{'━'*60}")
    print("  ✅ Task Scheduler completed successfully!")
    print(f"{'━'*60}\n")

    return {"plan": plan, "kpis": kpis}


def main():
    parser = argparse.ArgumentParser(
        description="Task Scheduler Optimization System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Default greedy scheduler
  python main.py --engine greedy          # Explicit greedy
  python main.py --horizon 120            # 120-hour planning window
  python main.py --no-report              # Skip file output
        """
    )
    parser.add_argument("--tasks", default="data/tasks.csv", help="Path to tasks CSV")
    parser.add_argument("--resources", default="data/resources.csv", help="Path to resources CSV")
    parser.add_argument("--engine", default="greedy", choices=["greedy"], help="Scheduling engine")
    parser.add_argument("--horizon", type=int, default=168, help="Planning horizon in hours (default: 168 = 1 week)")
    parser.add_argument("--no-report", action="store_true", help="Skip saving output files")

    args = parser.parse_args()

    result = run_scheduler(
        tasks_csv=args.tasks,
        resources_csv=args.resources,
        engine=args.engine,
        horizon=args.horizon,
        save_report=not args.no_report,
    )
    return result


if __name__ == "__main__":
    main()
