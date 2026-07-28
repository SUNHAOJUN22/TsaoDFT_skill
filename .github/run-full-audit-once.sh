#!/usr/bin/env bash
set -euo pipefail
export GITHUB_TOKEN="${GH_TOKEN:-}"
exec bash .github/full-audit-once.sh
