#!/usr/bin/env bash
set -euo pipefail

set +e
python3 scripts/copilot_cli_doctor.py --format plain
status=$?
set -e

case "$status" in
  0)
    echo "copilot-cli doctor: ready"
    ;;
  10)
    echo "copilot-cli doctor: missing"
    echo "install docs: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli"
    ;;
  11)
    echo "copilot-cli doctor: install-required"
    echo "install docs: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli"
    ;;
  12)
    echo "copilot-cli doctor: auth-required"
    echo "run interactive sign-in/configuration for standalone Copilot CLI"
    ;;
  *)
    echo "copilot-cli doctor: unexpected status code $status"
    ;;
esac

exit "$status"
