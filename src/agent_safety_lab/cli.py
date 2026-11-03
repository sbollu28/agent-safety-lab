"""Run the synthetic offline evaluation and optionally save a JSON report."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .evaluator import evaluate, naive_keyword_baseline

def run(dataset: dict) -> dict:
    policy = dataset["trusted_policy"]
    rows = []
    for case in dataset["cases"]:
        expected = bool(case["expected_approval"])
        decision = evaluate(case["proposal"], policy)
        baseline = naive_keyword_baseline(case["proposal"])
        rows.append({
            "id": case["id"], "category": case["category"],
            "expected_approval": expected,
            "guardrail_approved": decision.approved,
            "guardrail_correct": decision.approved == expected,
            "guardrail_reasons": list(decision.reasons),
            "baseline_approved": baseline.approved,
            "baseline_correct": baseline.approved == expected,
        })
    def metrics(prefix: str):
        correct = sum(x[prefix + "_correct"] for x in rows)
        return {
            "correct": correct, "total": len(rows),
            "accuracy": round(correct / len(rows), 4) if rows else None,
            "unsafe_approvals": sum(not x["expected_approval"] and x[prefix + "_approved"] for x in rows),
            "false_blocks": sum(x["expected_approval"] and not x[prefix + "_approved"] for x in rows)
        }
    return {
        "dataset": dataset.get("name", "unnamed"),
        "guardrail": metrics("guardrail"), "keyword_baseline": metrics("baseline"),
        "cases": rows,
        "limitations": "Synthetic and hand-authored. No LLM was evaluated; no production safety claim."
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=Path("examples/synthetic_cases.json"))
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    report = run(json.loads(args.dataset.read_text(encoding="utf-8")))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Guardrail:", report["guardrail"])
    print("Keyword baseline:", report["keyword_baseline"])

if __name__ == "__main__":
    main()
