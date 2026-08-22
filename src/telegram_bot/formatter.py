"""Telegram message formatting utilities."""

from typing import Dict, Any
from datetime import datetime, timezone


def format_market_status(provider_info: Dict[str, Any], price_info: Dict[str, Any], budget_status: Dict[str, Any]) -> str:
    """Format market status message for Telegram."""
    status = provider_info.get('status', 'UNKNOWN')
    status_emoji = '✓' if status == 'HEALTHY' else '⚠' if status == 'WARNING' else '❌'

    price = price_info.get('price', 'N/A')
    timestamp = price_info.get('timestamp', 'N/A')

    message = (
        f"🟡 **XAUUSD MARKET STATUS**\n\n"
        f"**Provider:** Twelve Data\n"
        f"**Symbol:** XAU/USD\n"
        f"**Latest Price:** {price}\n"
        f"**Data Timestamp:** {timestamp}\n"
        f"**Provider Health:** {status_emoji} {status}\n\n"
        f"**API Budget:**\n"
        f"• Requests today: {budget_status.get('requests_today', 0)}\n"
        f"• Credits used: {budget_status.get('estimated_credits_used', 0)}\n"
        f"• Remaining budget: {budget_status.get('remaining_budget', 0)}\n"
        f"• Daily limit: {budget_status.get('daily_api_budget', 700)}\n\n"
        f"**Timeframes:** 4H ✓ | 1H ✓ | 15M ✓ | 5M ✓ | 1M ON-DEMAND"
    )
    return message


def format_bot_status(provider_info: Dict[str, Any], budget_status: Dict[str, Any], startup_time: str) -> str:
    """Format bot status message for Telegram."""
    status = provider_info.get('status', 'UNKNOWN')
    status_emoji = '✓' if status == 'HEALTHY' else '⚠' if status == 'WARNING' else '❌'

    message = (
        f"🤖 **BOT STATUS**\n\n"
        f"**Startup Time:** {startup_time}\n"
        f"**Provider Status:** {status_emoji} {status}\n"
        f"**XAU/USD Status:** {status_emoji} {status}\n\n"
        f"**API Budget:**\n"
        f"• Daily limit: {budget_status.get('daily_api_budget', 700)}\n"
        f"• Safety reserve: {budget_status.get('safety_reserve', 100)}\n"
        f"• Requests today: {budget_status.get('requests_today', 0)}\n"
        f"• Credits used: {budget_status.get('estimated_credits_used', 0)}\n"
        f"• Remaining: {budget_status.get('remaining_budget', 0)}\n"
        f"• Cache hits: {budget_status.get('cache_hits', 0)}\n"
        f"• Cache misses: {budget_status.get('cache_misses', 0)}\n"
        f"• Rate limit errors: {budget_status.get('rate_limit_errors', 0)}\n"
        f"• Last update: {budget_status.get('last_successful_request', 'Never')}"
    )
    return message


def format_analysis_report(result: Dict[str, Any]) -> str:
    """Format analysis report for Telegram."""
    data_status = result.get('data_status', 'UNKNOWN')

    # Handle error states
    if data_status != 'OK':
        return f"❌ **ANALYSIS ERROR**\n\n{data_status}"

    action = result.get('action', 'WAIT')
    direction = result.get('direction', 'NEUTRAL')
    score = result.get('setup_score', {}).get('score', 0)
    grade = result.get('setup_score', {}).get('grade', 'NO TRADE')
    rr = result.get('rr', {}).get('rr', 0)

    entry = result.get('entry', {}).get('entry_price', 'N/A')
    sl = result.get('stop_loss', {}).get('stop_loss', 'N/A')
    tp1 = result.get('tp', {}).get('tp1', 'N/A')
    tp2 = result.get('tp', {}).get('tp2', 'N/A')

    htf_bias = result.get('htf_bias', {})
    regime = result.get('market_regime', {}).get('regime', 'UNKNOWN')
    session = result.get('session', {}).get('session_name', 'UNKNOWN')

    message = (
        f"🟡 **XAUUSD — SMC SETUP REPORT**\n\n"
        f"**HTF Bias**\n"
        f"• 4H: {htf_bias.get('4h', 'NEUTRAL')}\n"
        f"• 1H: {htf_bias.get('1h', 'NEUTRAL')}\n\n"
        f"**Market Conditions**\n"
        f"• Regime: {regime}\n"
        f"• Session: {session}\n\n"
        f"**Setup Quality**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"**SCORE:** {score}/100\n"
        f"**GRADE:** {grade}\n"
        f"**RR:** {rr}:1\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"**Setup Details**\n"
        f"• Direction: {direction}\n"
        f"• Entry: {entry}\n"
        f"• Stop Loss: {sl}\n"
        f"• TP1: {tp1}\n"
        f"• TP2: {tp2}\n\n"
        f"**Action:** {action}\n\n"
        f"⚠️ ANALYSIS ONLY — No automatic trade execution"
    )
    return message
