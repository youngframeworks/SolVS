#!/usr/bin/env python3
"""Start helper for offline mode: starts Foundry (optional), runs validation and tests.

Usage:
  python3 start.py --all
  python3 start.py --start-foundry --wait-ready --validate --test --discovery
"""
import argparse
import os
import shlex
import subprocess
import sys
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
            os.environ.setdefault(k, v)


def sh(cmd, capture=False, check=True, env=None):
    print(f"$ {cmd}")
    if capture:
        return subprocess.run(cmd, shell=True, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    else:
        return subprocess.run(cmd, shell=True, check=check, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Start foundry, wait, validate, run tests and discovery")
    parser.add_argument("--start-foundry", action="store_true")
    parser.add_argument("--wait-ready", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--test", action="store_true", help="Run model batch tests")
    parser.add_argument("--discovery", action="store_true", help="Run agents discovery test (requires provider configured for full JSON output)")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode (sets COPILOT_OFFLINE=true)")
    args = parser.parse_args()

    if args.all:
        args.start_foundry = True
        args.wait_ready = True
        args.validate = True
        args.test = True
        args.discovery = False
        args.offline = True

    # Load .env if present
    env_path = os.path.join(ROOT, ".env")
    load_env_file(env_path)

    if args.offline:
        os.environ.setdefault("COPILOT_OFFLINE", "true")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    logfile = os.path.join(LOG_DIR, f"start_{timestamp}.log")
    print(f"Logging to {logfile}")

    def log_run(cmd, capture=False, env=None):
        with open(logfile, "a", encoding="utf-8") as out:
            out.write(f"$ {cmd}\n")
            out.flush()
            if capture:
                proc = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
                out.write(proc.stdout or "")
                out.write("\n")
                return proc
            else:
                proc = subprocess.run(cmd, shell=True, check=False, env=env)
                out.write(f"exit={proc.returncode}\n")
                return proc

    try:
        if args.start_foundry:
            print("Starting Foundry local (bootstrap)...")
            log_run(f"bash {shlex.quote(os.path.join(ROOT, 'scripts', 'foundry_local_control.sh'))} start --ensure")

        if args.wait_ready:
            print("Waiting for Foundry to become ready...")
            # poll status
            status_cmd = f"bash {shlex.quote(os.path.join(ROOT, 'scripts', 'foundry_local_control.sh'))} status"
            for _ in range(30):
                r = log_run(status_cmd, capture=True)
                out = (r.stdout or "")
                if '"ready": true' in out:
                    print("Foundry is ready")
                    break
                print("Not ready yet, sleeping 2s")
                import time

                time.sleep(2)
            else:
                print("Foundry did not become ready in time")

        if args.validate:
            print("Running agent metadata validation...")
            log_run(f"python3 {shlex.quote(os.path.join(ROOT, 'scripts', 'validate_agents.py'))}")

        if args.test:
            print("Running model batch test...")
            log_run(f"export COPILOT_OFFLINE=${{COPILOT_OFFLINE:-}} && python3 {shlex.quote(os.path.join(ROOT, 'scripts', 'test_qwen2b_batch.py'))}")

        if args.discovery:
            print("Running agents discovery test (may require COPILOT_PROVIDER_BASE_URL)")
            log_run(f"export COPILOT_OFFLINE=${{COPILOT_OFFLINE:-}} && bash {shlex.quote(os.path.join(ROOT, 'scripts', 'test_agents_discovery.sh'))}")

    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(1)

    print(f"Start sequence complete. See {logfile} for details")


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
