#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "runtime" / "reports"


def utc_timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def latest_json(pattern: str):
    matches = sorted(REPORTS.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def load_json(path: Path | None):
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(title: str, task: str, route_summary: dict | None, cycle_summary: dict | None) -> str:
    lines = [
        f"# {title}",
        "",
        f"Task: {task}",
        "",
        "## Summary",
    ]

    if route_summary:
        lines.extend(
            [
                f"- Route rule: {route_summary.get('rule', 'unknown')}",
                f"- Route: {' -> '.join(route_summary.get('route', []))}",
                "- Dispatch targets:",
            ]
        )
        for dispatch in route_summary.get("dispatch", []):
            lines.append(
                f"  - {dispatch['agent']} via {dispatch['provider']} using MCP [{', '.join(dispatch['mcpServers'])}]"
            )
    else:
        lines.append("- No route summary available")

    lines.extend(["", "## Validation Artifacts"])
    if cycle_summary:
        for result in cycle_summary.get("results", []):
            lines.append(f"- Tick {result['tick']}: route rc={result['routeReturnCode']}")
    else:
        lines.append("- No cycle summary available")

    lines.extend(
        [
            "",
            "## Proposed Pull Request Body",
            "```markdown",
            f"## Automated proposal for: {task}",
            "",
            "### What changed",
            "- Generated route plan and dispatch metadata",
            "- Ran autonomous governance cycle in proposal mode",
            "- Produced machine-readable reports for review",
            "",
            "### Review checklist",
            "- [ ] Confirm selected route is correct",
            "- [ ] Confirm MCP targets are reachable in your environment",
            "- [ ] Approve or reject any follow-on apply action",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Build PR-ready proposal markdown from latest reports")
    parser.add_argument("--title", required=True, help="Proposal title")
    parser.add_argument("--task", required=True, help="Task summary")
    args = parser.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    route_summary = load_json(latest_json("route_summary_*.json"))
    cycle_summary = load_json(latest_json("autonomous_cycle_latest.json"))
    timestamp = utc_timestamp()
    content = render_markdown(args.title, args.task, route_summary, cycle_summary)
    out = REPORTS / f"proposal_{timestamp}.md"
    out.write_text(content, encoding="utf-8")
    latest = REPORTS / "proposal_latest.md"
    latest.write_text(content, encoding="utf-8")
    subprocess.run(
        ["python3", "scripts/provider_badges.py", "--proposal", str(latest.relative_to(ROOT))],
        cwd=ROOT,
        check=False,
    )
    print(out)


if __name__ == "__main__":
    main()
