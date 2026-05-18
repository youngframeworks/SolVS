#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
outdir="${PWD}/runtime/logs/parallel-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${outdir}"

echo "Starting SolManager (autopilot) and Fleet (research) in parallel"
bash "${script_dir}/run_solmanager_autopilot.sh" "$@" >"${outdir}/solmanager.log" 2>&1 &
pid1=$!
echo "SolManager PID=${pid1} -> ${outdir}/solmanager.log"

bash "${script_dir}/run_fleet_research.sh" "$@" >"${outdir}/fleet.log" 2>&1 &
pid2=$!
echo "Fleet PID=${pid2} -> ${outdir}/fleet.log"

wait ${pid1}
rc1=$?
wait ${pid2}
rc2=$?

echo "SolManager exit=${rc1}, Fleet exit=${rc2}"
if [ ${rc1} -ne 0 ] || [ ${rc2} -ne 0 ]; then
  echo "One or more processes failed. See logs in ${outdir}"
  exit $((rc1 || rc2))
fi

echo "Both processes completed successfully. Logs: ${outdir}"
exit 0
