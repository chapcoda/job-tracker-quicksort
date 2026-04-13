"""
Job Application Tracker — Quick Sort Visualizer
CISC 121 Project | Queen's University

Uses Quick Sort to rank job applications by urgency or priority score.
Visualizes each step of the algorithm so users can follow along.
"""

import gradio as gr
import json
from datetime import datetime, date

# ─────────────────────────────────────────────
# DATA STRUCTURES
# Each application is a dict:
# { company, role, deadline (YYYY-MM-DD), excitement (1-10), fit (1-10) }
# Priority Score = (excitement * 0.5) + (fit * 0.3) + (urgency_bonus * 0.2)
# ─────────────────────────────────────────────

SAMPLE_DATA = [
    {"company": "Shopify",      "role": "Backend Intern",      "deadline": "2026-05-10", "excitement": 9, "fit": 8},
    {"company": "RBC",          "role": "Data Analyst Co-op",  "deadline": "2026-04-20", "excitement": 6, "fit": 7},
    {"company": "Google",       "role": "SWE Intern",          "deadline": "2026-06-01", "excitement": 10,"fit": 6},
    {"company": "Local Startup","role": "Full Stack Dev",       "deadline": "2026-04-15", "excitement": 7, "fit": 9},
    {"company": "TD Bank",      "role": "IT Analyst",          "deadline": "2026-05-25", "excitement": 5, "fit": 6},
    {"company": "Hootsuite",    "role": "Product Intern",      "deadline": "2026-05-05", "excitement": 8, "fit": 8},
]


def days_until(deadline_str: str) -> int:
    """Return number of days from today until the deadline."""
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        delta = (deadline - date.today()).days
        return delta
    except ValueError:
        return 999  # treat bad dates as far future


def compute_priority(app: dict) -> float:
    """
    Priority Score formula:
      - excitement weight: 50%  (how excited the applicant is)
      - fit weight:        30%  (how well the role fits skills)
      - urgency bonus:     20%  (closer deadline = higher bonus, max 10)

    Urgency bonus: 10 if deadline <= 7 days, scales down to 0 at 60+ days.
    Higher score = should apply SOONER.
    """
    excitement = float(app["excitement"])
    fit = float(app["fit"])
    days = days_until(app["deadline"])

    # Urgency: 10 points at 0 days, 0 points at 60+ days
    urgency = max(0.0, 10.0 * (1 - days / 60.0)) if days <= 60 else 0.0

    score = (excitement * 0.5) + (fit * 0.3) + (urgency * 0.2)
    return round(score, 2)


# ─────────────────────────────────────────────
# QUICK SORT IMPLEMENTATION (with step logging)
# No built-in sort functions used.
# ─────────────────────────────────────────────

def quick_sort(apps: list, key_fn, steps: list, low: int = 0, high: int = None) -> list:
    """
    Recursive Quick Sort.
    - Picks the LAST element as pivot.
    - Partitions into elements < pivot and >= pivot.
    - Records each comparison step for visualization.

    args:
        apps   : list of application dicts (sorted in-place)
        key_fn : function(app) -> comparable value
        steps  : list to append step-by-step snapshots to
        low    : left boundary index
        high   : right boundary index
    """
    if high is None:
        high = len(apps) - 1

    if low < high:
        pivot_idx = partition(apps, key_fn, steps, low, high)
        quick_sort(apps, key_fn, steps, low, pivot_idx - 1)
        quick_sort(apps, key_fn, steps, pivot_idx + 1, high)

    return apps


def partition(apps: list, key_fn, steps: list, low: int, high: int) -> int:
    """
    Lomuto partition scheme.
    - pivot = apps[high]
    - i tracks the boundary of 'smaller than pivot' elements
    - Swaps elements into correct sides
    """
    pivot = apps[high]
    pivot_val = key_fn(pivot)
    i = low - 1  # index of the last element smaller than pivot

    for j in range(low, high):
        current_val = key_fn(apps[j])

        # Record this comparison as a step
        steps.append({
            "action": "compare",
            "pivot": pivot["company"],
            "pivot_val": pivot_val,
            "comparing": apps[j]["company"],
            "comparing_val": current_val,
            "range": (low, high),
            "snapshot": [a["company"] for a in apps],
        })

        if current_val > pivot_val:
            # Current element belongs on the 'larger' side — swap
            i += 1
            apps[i], apps[j] = apps[j], apps[i]

            steps.append({
                "action": "swap",
                "a": apps[i]["company"],
                "b": apps[j]["company"],
                "snapshot": [a["company"] for a in apps],
            })

    # Place pivot in its final position
    apps[i + 1], apps[high] = apps[high], apps[i + 1]
    steps.append({
        "action": "place_pivot",
        "pivot": pivot["company"],
        "position": i + 1,
        "snapshot": [a["company"] for a in apps],
    })

    return i + 1


# ─────────────────────────────────────────────
# FORMATTING HELPERS
# ─────────────────────────────────────────────

def apps_to_table_md(apps: list, sort_key: str) -> str:
    """Render application list as a Markdown table with computed scores."""
    if sort_key == "Priority Score":
        key_fn = compute_priority
        sort_col = "Priority Score"
    else:
        key_fn = lambda a: -days_until(a["deadline"])  # negative = sooner = higher
        sort_col = "Days Left"

    header = f"| Rank | Company | Role | Deadline | Days Left | Excitement | Fit | {sort_col} |\n"
    header += "|------|---------|------|----------|-----------|------------|-----|" + "-" * (len(sort_col) + 2) + "|\n"

    rows = ""
    for i, app in enumerate(apps, 1):
        days = days_until(app["deadline"])
        days_str = f"{days}d" if days >= 0 else f"**PAST**"
        score = compute_priority(app) if sort_key == "Priority Score" else f"{days}d"
        rows += f"| {i} | {app['company']} | {app['role']} | {app['deadline']} | {days_str} | {app['excitement']}/10 | {app['fit']}/10 | **{score}** |\n"

    return header + rows


def steps_to_md(steps: list) -> str:
    """Convert step log into a readable Markdown trace."""
    if not steps:
        return "_No steps recorded._"

    lines = ["### 🔍 Quick Sort Step-by-Step Trace\n"]
    step_num = 1
    for s in steps:
        if s["action"] == "compare":
            lines.append(
                f"**Step {step_num}** — Compare `{s['comparing']}` (score: {s['comparing_val']}) "
                f"vs pivot `{s['pivot']}` (score: {s['pivot_val']})"
            )
        elif s["action"] == "swap":
            lines.append(f"**Step {step_num}** — 🔄 Swap `{s['a']}` ↔ `{s['b']}`")
        elif s["action"] == "place_pivot":
            lines.append(f"**Step {step_num}** — ✅ Pivot `{s['pivot']}` placed at position {s['position'] + 1}")

        lines.append(f"> Order: {' → '.join(s['snapshot'])}\n")
        step_num += 1

    return "\n".join(lines)


def validate_apps(apps_json: str):
    """Parse and validate user-entered JSON applications."""
    try:
        apps = json.loads(apps_json)
        if not isinstance(apps, list) or len(apps) == 0:
            return None, "❌ Please enter a list (array) of applications."
        for i, a in enumerate(apps):
            for field in ["company", "role", "deadline", "excitement", "fit"]:
                if field not in a:
                    return None, f"❌ Application #{i+1} is missing the '{field}' field."
            if not (1 <= int(a["excitement"]) <= 10):
                return None, f"❌ Excitement for '{a['company']}' must be 1–10."
            if not (1 <= int(a["fit"]) <= 10):
                return None, f"❌ Fit for '{a['company']}' must be 1–10."
            datetime.strptime(a["deadline"], "%Y-%m-%d")  # validates date format
        return apps, None
    except json.JSONDecodeError as e:
        return None, f"❌ Invalid JSON: {e}"
    except ValueError as e:
        return None, f"❌ Data error: {e}"


# ─────────────────────────────────────────────
# MAIN HANDLER
# ─────────────────────────────────────────────

def run_sort(apps_json: str, sort_key: str, show_steps: bool):
    """
    Main Gradio handler.
    1. Validate input
    2. Run Quick Sort with step logging
    3. Return sorted table + step trace
    """
    apps, error = validate_apps(apps_json)
    if error:
        return error, ""

    # Choose sort key function
    if sort_key == "Priority Score":
        key_fn = compute_priority
    else:  # Deadline Urgency
        key_fn = lambda a: -days_until(a["deadline"])

    steps = []
    sorted_apps = quick_sort([a.copy() for a in apps], key_fn, steps)

    result_table = "## ✅ Sorted Applications\n\n" + apps_to_table_md(sorted_apps, sort_key)
    result_table += f"\n\n_Sorted {len(sorted_apps)} applications using **Quick Sort** on **{sort_key}**. "
    result_table += f"Total comparisons/swaps recorded: {len(steps)} steps._"

    step_trace = steps_to_md(steps) if show_steps else "_Enable 'Show Sort Steps' to see the trace._"

    return result_table, step_trace


def load_sample():
    return json.dumps(SAMPLE_DATA, indent=2)


# ─────────────────────────────────────────────
# GRADIO UI
# ─────────────────────────────────────────────

with gr.Blocks(
    title="Job Application Tracker — Quick Sort",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"),
) as demo:

    gr.Markdown("""
# 📋 Job Application Tracker
### Powered by Quick Sort | CISC 121 Project

Organize your job or internship applications by **deadline urgency** or **priority score**.  
Quick Sort ranks them so you know exactly which application to tackle first.

**Priority Score formula:** `(Excitement × 0.5) + (Fit × 0.3) + (Urgency × 0.2)`  
*Higher score = apply sooner!*
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📥 Your Applications (JSON format)")
            apps_input = gr.Textbox(
                label="Applications JSON",
                lines=20,
                placeholder='[\n  {\n    "company": "Shopify",\n    "role": "Backend Intern",\n    "deadline": "2025-05-10",\n    "excitement": 9,\n    "fit": 8\n  }\n]',
                value=json.dumps(SAMPLE_DATA, indent=2),
            )

            sort_key = gr.Radio(
                choices=["Priority Score", "Deadline Urgency"],
                value="Priority Score",
                label="Sort By",
            )

            show_steps = gr.Checkbox(
                label="Show Sort Steps (step-by-step trace)",
                value=True,
            )

            with gr.Row():
                sample_btn = gr.Button("📂 Load Sample Data", variant="secondary")
                sort_btn = gr.Button("🚀 Sort My Applications!", variant="primary")

            gr.Markdown("""
**JSON Field Guide:**
| Field | Type | Description |
|-------|------|-------------|
| `company` | string | Company name |
| `role` | string | Job title |
| `deadline` | string | `YYYY-MM-DD` format |
| `excitement` | 1–10 | How excited you are |
| `fit` | 1–10 | How well you fit the role |
            """)

        with gr.Column(scale=2):
            gr.Markdown("### 📊 Results")
            result_output = gr.Markdown(value="_Results will appear here after sorting._")

            gr.Markdown("### 🔬 Algorithm Trace")
            steps_output = gr.Markdown(value="_Step-by-step Quick Sort trace will appear here._")

    # Wire up buttons
    sort_btn.click(
        fn=run_sort,
        inputs=[apps_input, sort_key, show_steps],
        outputs=[result_output, steps_output],
    )

    sample_btn.click(
        fn=load_sample,
        inputs=[],
        outputs=[apps_input],
    )

    gr.Markdown("""
---
### ℹ️ About Quick Sort
Quick Sort works by selecting a **pivot** element and partitioning the list into two halves:
- Elements with a **higher score** than the pivot (apply sooner)
- Elements with a **lower score** than the pivot (apply later)

This repeats recursively until the list is fully sorted.  
**Average time complexity: O(n log n)** — efficient even for large application lists!

*CISC 121 — Queen's University Computing*
    """)

if __name__ == "__main__":
    demo.launch()
