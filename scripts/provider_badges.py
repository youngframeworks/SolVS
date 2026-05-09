#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "runtime" / "reports"
START = "<!-- provider-badges:start -->"
END = "<!-- provider-badges:end -->"


def latest_route_summary() -> Path | None:
    matches = sorted(REPORTS.glob("route_summary_*.json"))
    if not matches:
        return None
    return matches[-1]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_provider_state(execution_item: dict) -> str:
    if execution_item.get("returncode", 1) != 0:
        return "error"

    outer_stdout = execution_item.get("stdout", "")
    try:
        outer = json.loads(outer_stdout) if outer_stdout else {}
    except Exception:
        outer = {}

    if outer.get("returncode", 0) != 0:
        return "error"

    nested_stdout = outer.get("stdout", "")
    try:
        nested = json.loads(nested_stdout) if nested_stdout else {}
    except Exception:
        nested = {}

    status = str(nested.get("status", "")).strip().lower()
    if status in {"fallback", "plan-only"}:
        return "plan-only"
    if status == "skipped":
        return "skipped"
    return "ready"


def merge_provider_states(route_summary: dict) -> dict[str, str]:
    execution = route_summary.get("execution", [])
    provider_states: dict[str, str] = {}
    priority = {"error": 4, "plan-only": 3, "skipped": 2, "ready": 1}

    for item in execution:
        provider = item.get("provider", "unknown")
        state = normalize_provider_state(item)
        current = provider_states.get(provider)
        if current is None or priority[state] > priority[current]:
            provider_states[provider] = state

    if not provider_states:
        for dispatch in route_summary.get("dispatch", []):
            provider_states.setdefault(dispatch.get("provider", "unknown"), "ready")

    return provider_states


def badge(provider: str, state: str) -> str:
    color = {
        "ready": "brightgreen",
        "plan-only": "yellow",
        "skipped": "lightgrey",
        "error": "red",
    }.get(state, "blue")
    provider_label = quote(provider.replace("_", "-"))
    state_label = quote(state)
    return f"![{provider}-{state}](https://img.shields.io/badge/{provider_label}-{state_label}-{color})"


def build_section(route_summary_path: Path, provider_states: dict[str, str]) -> str:
    lines = [
        START,
        "## Provider Status Badges",
        "",
    ]
    for provider in sorted(provider_states.keys()):
        lines.append(badge(provider, provider_states[provider]))
    lines.extend([
        "",
        f"Source: {route_summary_path.relative_to(ROOT)}",
        END,
    ])
    return "\n".join(lines)


def upsert_badges(proposal_path: Path, section: str) -> None:
    text = proposal_path.read_text(encoding="utf-8") if proposal_path.exists() else ""
    if START in text and END in text:
        pre = text.split(START, 1)[0].rstrip()
        post = text.split(END, 1)[1].lstrip()
        new_text = f"{pre}\n\n{section}\n\n{post}".strip() + "\n"
    else:
        new_text = f"{text.rstrip()}\n\n{section}\n".lstrip("\n")
    proposal_path.write_text(new_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write provider status badges into proposal markdown")
    parser.add_argument("--proposal", default="runtime/reports/proposal_latest.md")
    args = parser.parse_args()

    proposal_path = ROOT / args.proposal
    route_path = latest_route_summary()
    if route_path is None:
        raise SystemExit("no route summary found")

    route_summary = load_json(route_path)
    provider_states = merge_provider_states(route_summary)
    section = build_section(route_path, provider_states)
    upsert_badges(proposal_path, section)
    print(proposal_path)


if __name__ == "__main__":
    main()
