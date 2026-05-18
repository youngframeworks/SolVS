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
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


def run(cmd, capture=False, check=False, env=None):
    print(f"> {cmd}")
    e = os.environ.copy()
    if env:
        e.update(env)
    if capture:
        return subprocess.run(cmd, shell=True, check=check, cwd=ROOT, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return subprocess.run(cmd, shell=True, check=check, cwd=ROOT, env=e)


def create_venv_and_install(venv_dir=".venv", req_file="requirements-dev.txt"):
    venv_path = os.path.join(ROOT, venv_dir)
    if not os.path.isdir(venv_path):
        print(f"Creating venv at {venv_path}")
        run(f"python3 -m venv {shlex.quote(venv_path)}", check=True)
    activate = os.path.join(venv_path, "bin", "activate")
    if not os.path.exists(activate):
        raise RuntimeError("venv activation script not found")
    print("Installing dev requirements into venv")
    run(f"bash -lc 'source {shlex.quote(activate)} && python -m pip install --upgrade pip && python -m pip install -r {shlex.quote(req_file)}'", check=False)


def start_foundry():
    print("Starting Foundry local (bootstrap)")
    run(f"bash scripts/foundry_local_control.sh start --ensure")


def wait_for_foundry(timeout_seconds=60):
    print(f"Waiting up to {timeout_seconds}s for Foundry to be ready")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        cp = run("bash scripts/foundry_local_control.sh status", capture=True)
        out = cp.stdout or ""
        print('\n'.join(out.splitlines()[:10]))
        if '"ready": true' in out:
            print("Foundry ready")
            return True
        time.sleep(2)
    print("Foundry not ready within timeout")
    return False


def validate_agents():
    print("Validating AGENTS.md")
    run("python3 scripts/validate_agents.py", check=False)


def run_model_tests():
    print("Running model batch tests")
    run("python3 scripts/test_qwen2b_batch.py", check=False)


def run_discovery():
    print("Running agents discovery script")
    run("bash scripts/test_agents_discovery.sh", check=False)


def open_vscode():
    print("Opening VS Code")
    run("code .", check=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="Create venv and install dev requirements")
    parser.add_argument("--foundry-start", action="store_true")
    parser.add_argument("--wait-ready", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--discovery", action="store_true")
    parser.add_argument("--open", action="store_true", help="Open repository in VS Code")
    parser.add_argument("--offline", action="store_true", help="Set COPILOT_OFFLINE=true in env")
    parser.add_argument("--all", action="store_true", help="Run setup + foundry start + wait + validate + test (offline)")
    args = parser.parse_args()

    if args.all:
        args.setup = True
        args.foundry_start = True
        args.wait_ready = True
        args.validate = True
        args.test = True
        args.offline = True

    load_env_file(os.path.join(ROOT, ".env"))
    if args.offline:
        os.environ.setdefault("COPILOT_OFFLINE", "true")

    # Logging
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    logfile = os.path.join(LOG_DIR, f"start_{timestamp}.log")
    print(f"Logs will be appended to {logfile}")

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
