#!/usr/bin/env python3
"""Start helper for offline mode: manages venv, Foundry, validation, tests, and optional editor open.

Features:
- --setup : create venv and install requirements-dev.txt
- --foundry-start : start Foundry local (bootstrap)
- --wait-ready : wait for Foundry readiness
- --validate : run `scripts/validate_agents.py`
- --test : run `scripts/test_qwen2b_batch.py`
- --discovery : run `scripts/test_agents_discovery.sh`
- --open : open repository in VS Code after setup
- --offline : set `COPILOT_OFFLINE=true` in the environment
- --all : run a safe default offline sequence (setup + foundry start + wait + validate + test)
"""
import argparse
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT, "runtime", "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
    if __name__ == "__main__":
        main()
    # Execute requested actions
    if args.setup:
        create_venv_and_install()

    if args.foundry_start:
        start_foundry()

    if args.wait_ready:
        wait_for_foundry()

    if args.validate:
        validate_agents()

    if args.test:
        run_model_tests()

    if args.discovery:
        run_discovery()

    if args.open:
        open_vscode()

    print("start.py completed")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
start.py - convenience runner for local Foundry + Copilot checks

Usage:
  python3 start.py --foundry-start
  python3 start.py --doctor
  python3 start.py --test
  python3 start.py --all

This script loads `.env` into the process environment (simple KEY=VALUE parser)
and invokes the repository helper scripts.
"""
import os
import subprocess
import argparse
import shlex
import sys


# Repository root (this file lives at repo root)
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def load_env(path=".env"):
    """Load simple KEY=VALUE pairs from a `.env` file into os.environ.

    Supports lines like `KEY=VALUE` and `export KEY=VALUE`. Ignores comments.
    Does not perform shell evaluation; values are used verbatim.
    """
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            os.environ.setdefault(k, v)


def run_cmd(cmd, check=False):
    """Run a shell command from the repository root, returning CompletedProcess."""
    print(f"> {cmd}")
    env = os.environ.copy()
    return subprocess.run(cmd, shell=True, check=check, cwd=REPO_ROOT, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundry-start", action="store_true")
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    load_env()

    steps = []
    if args.all or args.foundry_start:
        steps.append(("Foundry quick start", "bash scripts/foundry_local_quick_start.sh"))
    if args.all or args.doctor:
        steps.append(("Copilot doctor", "python3 scripts/copilot_cli_doctor.py --format plain"))
    if args.all or args.test:
        steps.append(("Model test", "python3 scripts/test_qwen2b_batch.py"))

    if not steps:
        parser.print_help()
        sys.exit(0)

    failures = []
    for name, cmd in steps:
        print(f"\n== Running: {name} ==")
        try:
            cp = run_cmd(cmd)
            if cp.returncode != 0:
                print(f"{name} exited with code {cp.returncode}")
                failures.append((name, cp.returncode))
        except subprocess.CalledProcessError as e:
            print(f"{name} failed: {e}")
            failures.append((name, getattr(e, "returncode", -1)))

    print("\n== Summary ==")
    if not failures:
        print("All steps completed successfully.")
        sys.exit(0)
    else:
        for n, code in failures:
            print(f"- {n}: failed (code {code})")
        sys.exit(1)


if __name__ == "__main__":
    main()
