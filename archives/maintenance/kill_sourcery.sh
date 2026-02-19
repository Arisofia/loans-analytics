#!/usr/bin/env bash
set -euo pipefail

# Kill all processes that match 'sourcery'
PIDS=$(pgrep -f sourcery || true)

if [[ -z $PIDS ]]; then
	echo "No se encontró proceso 'sourcery'"
	exit 0
fi

echo "Deteniendo procesos sourcery: $PIDS"
# First try graceful termination
kill $PIDS || true
sleep 2

# If still running, force kill
PIDS_REMAINING=$(pgrep -f sourcery || true)
if [[ -n $PIDS_REMAINING ]]; then
	echo "Forzando detención de: $PIDS_REMAINING"
	sudo kill -9 $PIDS_REMAINING || true
fi

echo "Operación completada."
