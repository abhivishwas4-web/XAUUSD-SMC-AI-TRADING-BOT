#!/usr/bin/env bash
set -euo pipefail

echo "== Python compile check =="
python -m compileall src

echo "\n== Run pytest -v =="
pytest -v | tee pytest_v.txt

echo "\n== Run pytest --tb=short =="
pytest --tb=short | tee pytest_tb_short.txt

echo "\n== Quick secrets scan (grep heuristics) =="
# This is a heuristic grep. Review results manually. It intentionally does not print file contents, only matches.
{ git grep -nE "(TWELVE|TWELVEDATA|TWELVE_DATA|TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID|TWELVE|API_KEY|SECRET|TOKEN)" || true; } > secrets_grep.txt

echo "\nRun completed. Outputs: pytest_v.txt pytest_tb_short.txt secrets_grep.txt"
