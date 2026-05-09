#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = ROOT / "config" / "router.rules.json"
RUNTIME = ROOT / "runtime"
EVOLUTION_LOG = ROOT / "OS_EVOLUTION_LOG.md"


def load_rules():
    with RULES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_rules(data):
    with RULES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def write_backup(data, ts: str) -> Path:
    backup = RUNTIME / "reports" / f"router_rules_backup_{ts}.json"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return backup


def append_evolution_log(ts: str, changed: bool, backup: Path | None):
    if not EVOLUTION_LOG.exists():
        EVOLUTION_LOG.write_text("# OS Evolution Log\n\n", encoding="utf-8")
    lines = [
        f"## {ts}",
        "- Scope: SolVS fleet routing evolution",
        f"- Changed: {'yes' if changed else 'no'}",
        f"- Rules file: {RULES_FILE.relative_to(ROOT)}",
    ]
    if backup is not None:
        lines.append(f"- Backup: {backup.relative_to(ROOT)}")
        lines.append(f"- Rollback: cp {backup.relative_to(ROOT)} {RULES_FILE.relative_to(ROOT)}")
    else:
        lines.append("- Backup: none")
    lines.append("")
    with EVOLUTION_LOG.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def propose(data):
    rules = data.get("rules", [])
    count = len(rules)
    opportunity = "add specialized rule" if count < 5 else "compress overlapping rules"
    impact = "medium" if count < 5 else "low"
    return opportunity, impact


def write_report(opportunity: str, impact: str, applied: bool, changed: bool, backup: Path | None):
    ts = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out = RUNTIME / "reports" / f"self_evolve_{ts}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Self-Evolve Report {ts}",
        "",
        f"Mode: {'apply' if applied else 'proposal'}",
        f"Changed: {'yes' if changed else 'no'}",
        f"Opportunity: {opportunity}",
        f"Impact: {impact}",
        "",
        "Gate:",
        "- apply mode requires approval token APPLY_EVOLUTION",
    ]
    if backup is not None:
        lines.extend([
            "",
            "Rollback:",
            f"- cp {backup.relative_to(ROOT)} {RULES_FILE.relative_to(ROOT)}",
        ])
    lines.extend([
        "",
        "Governance:",
        f"- evolution log: {EVOLUTION_LOG.relative_to(ROOT)}",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def apply_evolution(data):
    if any(r.get("id") == "security-hardening" for r in data.get("rules", [])):
        return False, None
    ts = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    backup = write_backup(data, ts)
    data.setdefault("rules", []).append(
        {
            "id": "security-hardening",
            "matchAny": ["security", "policy", "compliance", "hardening"],
            "route": ["SolManager", "SolOSReviewer"]
        }
    )
    write_rules(data)
    return True, backup


def main():
    parser = argparse.ArgumentParser(description="Proposal-first self-evolve loop")
    parser.add_argument("--apply", action="store_true", help="Apply evolution")
    parser.add_argument("--approval-token", default="", help="Must be APPLY_EVOLUTION for apply")
    args = parser.parse_args()

    data = load_rules()
    opp, impact = propose(data)
    changed = False
    backup = None

    if args.apply:
        if args.approval_token != "APPLY_EVOLUTION":
            raise SystemExit("apply denied: approval token mismatch")
        changed, backup = apply_evolution(data)
        append_evolution_log(dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ"), changed, backup)

    report = write_report(opp, impact, args.apply, changed, backup)
    print("report:", report)


if __name__ == "__main__":
    main()
