#!/usr/bin/env python3
"""Start Foundry Local web service via the foundry-local-sdk and write meta.

Usage:
    python3 scripts/foundry_local_sdk_launcher.py [--model ALIAS] [--stop] [--status]

Defaults:
    --model  phi-4-mini   (override with FOUNDRY_LOCAL_MODEL env var)
    Endpoint written to runtime/logs/foundry-local.meta.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_FILE = ROOT / "runtime" / "logs" / "foundry-local.meta.json"
DEFAULT_MODEL = os.environ.get("FOUNDRY_LOCAL_MODEL", "qwen3.5-2b")

# Ensure the SDK is importable whether installed --break-system-packages or in venv
_SDK_SITE = Path.home() / ".local" / "lib"
for _p in _SDK_SITE.glob("python*/site-packages"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _write_meta(mode: str, endpoint: str, model: str) -> None:
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(
        json.dumps(
            {
                "mode": mode,
                "endpoint": endpoint,
                "model": model,
                "pidFile": str(ROOT / "runtime" / "logs" / "foundry-local.pid"),
                "logFile": str(ROOT / "runtime" / "logs" / "foundry-local.log"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _probe(endpoint: str, timeout: int = 3) -> bool:
    for suffix in ("/v1/models", "/health", "/openai/v1/models", "/mcp"):
        try:
            with urllib.request.urlopen(endpoint.rstrip("/") + suffix, timeout=timeout) as r:
                if r.status < 500:
                    return True
        except Exception:
            pass
    return False


def cmd_status(endpoint: str) -> None:
    if _probe(endpoint):
        print(f"foundry-local is READY at {endpoint}")
    else:
        print(f"foundry-local is NOT ready at {endpoint}")


def cmd_stop(manager) -> None:  # type: ignore[valid-type]
    manager.stop_web_service()
    print("foundry-local service stopped")


def cmd_start(model_alias: str) -> None:
    try:
        from foundry_local_sdk import Configuration, FoundryLocalManager
    except ImportError as exc:
        print(f"[ERROR] foundry-local-sdk not importable: {exc}", file=sys.stderr)
        print("Run: pip install --break-system-packages foundry-local-sdk", file=sys.stderr)
        sys.exit(1)

    bind_url = "http://127.0.0.1:5272"
    config = Configuration(
        app_name="SolVS",
        web=Configuration.WebService(urls=bind_url),
    )
    FoundryLocalManager.initialize(config)
    mgr = FoundryLocalManager.instance

    # Verify the model exists in catalog
    model = mgr.catalog.get_model(model_alias)
    if model is None:
        available = [getattr(m, "alias", str(m)) for m in mgr.catalog.list_models()]
        print(f"[ERROR] Model '{model_alias}' not in catalog.", file=sys.stderr)
        print(f"Available: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting foundry-local service with model: {model_alias}")
    mgr.start_web_service()
    endpoint = (mgr.urls[0] if mgr.urls else bind_url)

    # Wait up to 60 s for the endpoint to become ready
    print(f"Waiting for endpoint {endpoint} …", end="", flush=True)
    for _ in range(60):
        if _probe(endpoint, timeout=2):
            break
        print(".", end="", flush=True)
        time.sleep(1)
    else:
        print("\n[WARN] Service may not be fully ready yet.", file=sys.stderr)

    print(f"\nfoundry-local ready at {endpoint}")
    _write_meta("sdk", endpoint, model_alias)


def cmd_serve(model_alias: str) -> None:
    """Start the web service and block indefinitely (daemon mode)."""
    try:
        from foundry_local_sdk import Configuration, FoundryLocalManager
    except ImportError as exc:
        print(f"[ERROR] foundry-local-sdk not importable: {exc}", file=sys.stderr)
        sys.exit(1)

    bind_url = "http://127.0.0.1:5272"
    config = Configuration(
        app_name="SolVS",
        web=Configuration.WebService(urls=bind_url),
    )
    FoundryLocalManager.initialize(config)
    mgr = FoundryLocalManager.instance

    model = mgr.catalog.get_model(model_alias)
    if model is None:
        available = [getattr(m, "alias", str(m)) for m in mgr.catalog.list_models()]
        print(f"[ERROR] Model '{model_alias}' not in catalog.", file=sys.stderr)
        print(f"Available: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    print(f"[foundry-local] starting service with model: {model_alias}")
    mgr.start_web_service()
    endpoint = mgr.urls[0] if mgr.urls else bind_url

    print(f"[foundry-local] waiting for {endpoint} …", end="", flush=True)
    for _ in range(60):
        if _probe(endpoint, timeout=2):
            break
        print(".", end="", flush=True)
        time.sleep(1)
    else:
        print("\n[WARN] endpoint not responding after 60s", file=sys.stderr)

    print(f"\n[foundry-local] ready at {endpoint}  (model={model_alias})")
    _write_meta("sdk", endpoint, model_alias)
    # Download model if not cached, then load it
    if not model.is_cached:
        print(f"[foundry-local] downloading model {model_alias} (first run) …")
        model.download(progress_callback=lambda p: print(f"\r  {p:.0%}", end="", flush=True))
        print()
    print(f"[foundry-local] loading model {model_alias} into memory …")
    model.load()
    print(f"[foundry-local] model {model_alias} loaded ✓")
    # Write PID for control scripts
    pid_file = META_FILE.parent / "foundry-local.pid"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")

    import signal
    stop_event = __import__("threading").Event()

    def _handle_sig(*_):
        print("\n[foundry-local] shutting down…")
        try:
            mgr.stop_web_service()
        except Exception:
            pass
        pid_file.unlink(missing_ok=True)
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_sig)
    signal.signal(signal.SIGINT, _handle_sig)

    print("[foundry-local] serving — send SIGTERM or Ctrl-C to stop")
    stop_event.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Foundry Local SDK launcher")
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="Start the service (one-shot, non-blocking)")
    p_start.add_argument("--model", default=DEFAULT_MODEL, help="Model alias to load")

    p_serve = sub.add_parser("serve", help="Start and block (daemon/foreground mode)")
    p_serve.add_argument("--model", default=DEFAULT_MODEL, help="Model alias to load")

    sub.add_parser("stop", help="Stop the service")

    p_status = sub.add_parser("status", help="Check if service is ready")
    p_status.add_argument(
        "--endpoint", default="http://127.0.0.1:5272", help="Endpoint to probe"
    )

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args.model)
    elif args.command == "serve":
        cmd_serve(args.model)
    elif args.command == "stop":
        try:
            from foundry_local_sdk import Configuration, FoundryLocalManager
        except ImportError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            sys.exit(1)
        config = Configuration(app_name="SolVS")
        FoundryLocalManager.initialize(config)
        cmd_stop(FoundryLocalManager.instance)
    elif args.command == "status":
        cmd_status(args.endpoint)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
