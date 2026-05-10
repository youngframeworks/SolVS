#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    print(f"$ {' '.join(cmd)}")
    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip())
    return proc.returncode


def latest_matching(pattern: str):
    matches = sorted((ROOT / "runtime" / "reports").glob(pattern))
    if not matches:
        return None
    return matches[-1]


def load_fleet_config():
    """Load fleet.json to check autoSelfHeal and autoSelfEvolve flags."""
    config_path = ROOT / "config" / "fleet.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_cycle_report(task: str, ticks: int, tick_results: list[dict], proposal_file: Path | None):
    report_dir = ROOT / "runtime" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "autonomous_cycle_latest.json"
    payload = {
        "task": task,
        "ticks": ticks,
        "executeProviders": any("providerExecution" in result for result in tick_results),
        "results": tick_results,
        "proposalFile": str(proposal_file.relative_to(ROOT)) if proposal_file else None,
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Run autonomous route/heal/evolve loop with auto self-healing & evolution")
    parser.add_argument("--task", required=True, help="Task to route")
    parser.add_argument("--ticks", type=int, default=3, help="Number of loop iterations")
    parser.add_argument(
        "--execute-providers",
        action="store_true",
        help="Invoke provider adapters during each route tick",
    )
    parser.add_argument(
        "--proposal-title",
        default="Autonomous Fleet Proposal",
        help="Title for generated PR-ready proposal",
    )
    args = parser.parse_args()
    os.environ["FLEET_EXECUTION_MODE"] = "execute" if args.execute_providers else "proposal"

    # Load auto self-heal/evolve flags from config
    fleet_config = load_fleet_config()
    auto_heal = fleet_config.get("autoSelfHeal", False)
    auto_evolve = fleet_config.get("autoSelfEvolve", False)
    
    print(f"[Config] autoSelfHeal={auto_heal}, autoSelfEvolve={auto_evolve}")
    print(f"[Autonomy] Running {args.ticks} ticks with local-first Foundry backend...")
    print()

    tick_results = []
    for tick in range(1, args.ticks + 1):
        print(f"=== Tick {tick}/{args.ticks} ===")
        route_cmd = [
            "python3",
            "scripts/route_task.py",
            "--task",
            args.task,
            "--write-summary",
        ]
        if args.execute_providers:
            route_cmd.append("--execute")
        code = run(route_cmd)
        tick_entry = {"tick": tick, "routeReturnCode": code}
        if args.execute_providers:
            tick_entry["providerExecution"] = "enabled"
        tick_results.append(tick_entry)
        
        # Auto self-heal: on failure OR if autoSelfHeal enabled
        if code != 0 or auto_heal:
            print(f"[Auto-Heal] Running self_heal.py (enabled={auto_heal}, failed={code != 0})...")
            heal_code = run(["python3", "scripts/self_heal.py"])
            tick_results[-1]["selfHealReturnCode"] = heal_code
        
        # Auto self-evolve: every 5 ticks OR if autoSelfEvolve enabled
        if tick % 5 == 0 or auto_evolve:
            print(f"[Auto-Evolve] Running self_evolve.py (enabled={auto_evolve}, tick%5={tick % 5 == 0})...")
            evolve_code = run(["python3", "scripts/self_evolve.py"])
            tick_results[-1]["selfEvolveReturnCode"] = evolve_code
        
        print()

    proposal_code = run([
        "python3",
        "scripts/proposal_pack.py",
        "--title",
        args.proposal_title,
        "--task",
        args.task,
    ])
    proposal_file = latest_matching("proposal_*.md") if proposal_code == 0 else None
    cycle_report = write_cycle_report(args.task, args.ticks, tick_results, proposal_file)
    print(f"✅ Cycle complete: {cycle_report}")


if __name__ == "__main__":
    main()
