#!/bin/bash
# Quick execution of comprehensive cleanup
set -e
cd "$(git rev-parse --show-toplevel)" || exit 1
bash archives/sessions/2026-01-cleanup/comprehensive_cleanup.sh
