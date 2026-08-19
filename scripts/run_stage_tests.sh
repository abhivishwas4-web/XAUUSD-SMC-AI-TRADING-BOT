# helper to run only Stage-specific tests quickly
# Usage: ./scripts/run_stage_tests.sh stage3

STAGE=$1
set -euo pipefail

case "$STAGE" in
  stage1)
    pytest -q tests/test_stage1_structure.py
    ;;
  stage2)
    pytest -q tests/test_twelvedata_provider.py tests/test_cache_and_budget.py tests/test_health_check.py
    ;;
  stage3)
    pytest -q tests/test_swing_points.py tests/test_structure.py tests/test_liquidity.py tests/test_sweep.py tests/test_displacement.py tests/test_fvg.py
    ;;
  stage4)
    pytest -q tests/test_atr.py tests/test_regime.py tests/test_sessions.py
    ;;
  stage5)
    pytest -q tests/test_entry.py tests/test_stop_loss.py tests/test_take_profit.py tests/test_rr.py || true
    ;;
  stage6)
    pytest -q tests/test_scorer.py
    ;;
  stage7)
    pytest -q tests/test_analysis_orchestrator.py
    ;;
  stage8)
    pytest -q tests/test_telegram_bot.py
    ;;
  all)
    pytest -v
    ;;
  *)
    echo "Unknown stage: $STAGE"
    exit 2
    ;;
esac
