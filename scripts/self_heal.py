#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
RUNTIME = ROOT / "runtime"
REQUIRED = [
    CONFIG / "fleet.json",
    CONFIG / "router.rules.json",
    CONFIG / "hooks.json",
    CONFIG / "mcp.servers.json",
    ROOT / ".github" / "agents" / "solmanager.agent.md",
]

TEMPLATES = {
    "config/fleet.json": json.dumps(
        {
            "fleetVersion": "0.1.0",
            "defaultProvider": "copilot-cli",
            "providers": {},
            "agents": [],
        },
        indent=2,
    )
    + "\n",
    "config/router.rules.json": json.dumps(
        {
            "rules": [],
            "fallbackRoute": ["SolOSRouter", "SolOSImplementer", "SolOSReviewer"],
        },
        indent=2,
    )
    + "\n",
    "config/hooks.json": json.dumps(
        {
            "hooks": {
                "preRoute": ["scripts/validate.sh", "scripts/check_policy_gate.sh"],
                "postRoute": ["scripts/log_plan.sh"],
                "onFailure": ["python3 scripts/self_heal.py"],
            }
        },
        indent=2,
    )
    + "\n",
    "config/mcp.servers.json": json.dumps({"servers": []}, indent=2) + "\n",
    ".github/agents/solmanager.agent.md": "---\nname: SolManager\ndescription: Sol OS orchestrator.\n---\n\n# SolManager\n\n## Responsibilities\n- Enforce governance and routing boundaries.\n",
}


def inspect():
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
    drift_score = min(100, len(missing) * 20)
    return drift_score, missing


def file_digest(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def write_report(drift_score: int, missing: list[str], applied: bool, applied_results: list[dict], skipped: list[str]):
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out = RUNTIME / "reports" / f"self_heal_{ts}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Self-Heal Report {ts}",
        "",
        f"Drift score: {drift_score}",
        f"Mode: {'apply' if applied else 'proposal'}",
        "",
        "Missing files:",
    ]
    if missing:
        lines.extend([f"- {m}" for m in missing])
    else:
        lines.append("- none")

    lines.extend([
        "",
        "Applied repairs:",
    ])
    if applied_results:
        for result in applied_results:
            lines.append(f"- {result['path']} sha256={result['sha256']}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "Skipped repairs:",
    ])
    if skipped:
        lines.extend([f"- {path}" for path in skipped])
    else:
        lines.append("- none")

    lines.extend([
        "",
        "Recommendation:",
        "- Apply only after human approval.",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def apply_missing(missing: list[str]):
    applied_results = []
    skipped = []
    for rel in missing:
        if rel not in TEMPLATES:
            skipped.append(rel)
            continue
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(TEMPLATES[rel], encoding="utf-8")
        applied_results.append({"path": rel, "sha256": file_digest(p)})
    return applied_results, skipped


def main():
    parser = argparse.ArgumentParser(description="Proposal-first self-heal loop")
    parser.add_argument("--apply", action="store_true", help="Apply fixes")
    parser.add_argument("--approval-token", default="", help="Must be APPLY_SELF_HEAL for apply")
    args = parser.parse_args()

    drift_score, missing = inspect()
    applied_results = []
    skipped = []
    if args.apply:
        if args.approval_token != "APPLY_SELF_HEAL":
            raise SystemExit("apply denied: approval token mismatch")
        applied_results, skipped = apply_missing(missing)
        drift_score, missing = inspect()

    report = write_report(drift_score, missing, args.apply, applied_results, skipped)
    print("drift_score:", drift_score)
    print("report:", report)


if __name__ == "__main__":
    main()
