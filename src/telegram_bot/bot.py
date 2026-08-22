"""Telegram bot implementation for XAUUSD SMC analysis."""

import logging
import os
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandContext, ContextTypes
from datetime import datetime, timezone

from src.utils.logger import get_logger
from src.utils.exceptions import DataError
from src.orchestrator.analysis_orchestrator import AnalysisOrchestrator
from src.telegram_bot.formatter import format_market_status, format_analysis_report, format_bot_status

logger = get_logger(__name__)


class XAUUSDTradingBot:
    """XAUUSD SMC Analysis Telegram Bot."""

    def __init__(self, token: str, chat_id: str, config: dict):
        """Initialize bot with token and chat ID.

        Args:
            token: Telegram bot token
            chat_id: Telegram chat ID for notifications
            config: Configuration dictionary
        """
        if not token or token == 'test_token':
            logger.warning('TELEGRAM_BOT_TOKEN not properly configured or is test token')
        if not chat_id or chat_id == 'test_chat_id':
            logger.warning('TELEGRAM_CHAT_ID not properly configured or is test chat ID')

        self.token = token
        self.chat_id = chat_id
        self.config = config
        self.app: Optional[Application] = None
        self.orchestrator = AnalysisOrchestrator(config)
        self.startup_time = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        message = (
            "🟡 **XAUUSD-SMC-AI-TRADING-BOT** (V1)\n\n"
            "Smart Money Concepts analysis for XAU/USD (Gold)\n\n"
            "**Capabilities:**\n"
            "• Real-time XAU/USD market analysis\n"
            "• SMC structure detection (4H → 1H → 15M → 5M)\n"
            "• Liquidity & sweep analysis\n"
            "• Entry/SL/TP calculation\n"
            "• Risk/Reward evaluation\n"
            "• Setup quality scoring\n\n"
            "**V1 Scope:**\n"
            "• ANALYSIS ONLY (no automatic trading)\n"
            "• Rule-based setup detection\n"
            "• No ML/AI in V1\n\n"
            "**Commands:**\n"
            "/help - Show all commands\n"
            "/market - XAU/USD market status\n"
            "/status - Bot & provider status\n"
            "/analyze - Run full SMC analysis\n"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info('User executed /start command')

    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        message = (
            "**XAUUSD-SMC-AI-TRADING-BOT Commands**\n\n"
            "/start - Show bot information\n"
            "/help - Show this help message\n"
            "/market - Display current XAU/USD market status\n"
            "/status - Display bot, provider, and API budget status\n"
            "/analyze - Run complete SMC analysis and generate setup report\n\n"
            "**About V1:**\n"
            "This is an analysis-only bot. No trades are executed.\n"
            "Market conditions can change rapidly. Always verify before trading."
        )
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info('User executed /help command')

    async def market_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /market command."""
        try:
            provider = self.orchestrator._get_provider()
            pinfo = provider.health_check()
            price_info = provider.get_current_price(self.orchestrator.mapped_symbol)
            budget_status = self.orchestrator.budget.status()

            message = format_market_status(pinfo, price_info, budget_status)
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info('User executed /market command')
        except Exception as e:
            logger.exception('Error in /market handler')
            error_msg = f"❌ **MARKET STATUS ERROR**\n\n{str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')

    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        try:
            provider = self.orchestrator._get_provider()
            pinfo = provider.health_check()
            budget_status = self.orchestrator.budget.status()

            message = format_bot_status(pinfo, budget_status, self.startup_time)
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info('User executed /status command')
        except Exception as e:
            logger.exception('Error in /status handler')
            error_msg = f"❌ **BOT STATUS ERROR**\n\n{str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')

    async def analyze_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analyze command."""
        try:
            # Run analysis
            result = self.orchestrator.analyze()

            # Format and send report
            message = format_analysis_report(result)
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info('User executed /analyze command')
        except Exception as e:
            logger.exception('Error in /analyze handler')
            error_msg = f"❌ **ANALYSIS ERROR**\n\n{str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')

    def setup_handlers(self) -> None:
        """Register command handlers with the application."""
        if not self.app:
            raise RuntimeError('Application not initialized. Call initialize() first.')

        self.app.add_handler(CommandContext('/start', self.start_handler))
        self.app.add_handler(CommandContext('/help', self.help_handler))
        self.app.add_handler(CommandContext('/market', self.market_handler))
        self.app.add_handler(CommandContext('/status', self.status_handler))
        self.app.add_handler(CommandContext('/analyze', self.analyze_handler))

    async def initialize(self) -> None:
        """Initialize and start the Telegram application."""
        logger.info('Initializing Telegram bot application...')

        try:
            self.app = Application.builder().token(self.token).build()
            self.setup_handlers()
            logger.info('Telegram bot application initialized successfully')
        except Exception as e:
            logger.exception('Failed to initialize Telegram bot application')
            raise

    async def run(self) -> None:
        """Start the bot polling."""
        if not self.app:
            await self.initialize()

        try:
            logger.info('Starting Telegram bot polling...')
            await self.app.run_polling()
        except Exception as e:
            logger.exception('Error during bot polling')
            raise


async def main_async(config: dict) -> None:
    """Main async entry point for the bot."""
    token = config.get('env', {}).get('TELEGRAM_BOT_TOKEN')
    chat_id = config.get('env', {}).get('TELEGRAM_CHAT_ID')

    if not token:
        logger.error('TELEGRAM_BOT_TOKEN not configured')
        raise ValueError('TELEGRAM_BOT_TOKEN is required')

    if not chat_id:
        logger.error('TELEGRAM_CHAT_ID not configured')
        raise ValueError('TELEGRAM_CHAT_ID is required')

    bot = XAUUSDTradingBot(token, chat_id, config)
    await bot.run()


def main(config: dict) -> None:
    """Synchronous wrapper for bot initialization."""
    import asyncio

    try:
        asyncio.run(main_async(config))
    except KeyboardInterrupt:
        logger.info('Bot interrupted by user')
    except Exception as e:
        logger.exception('Fatal error in bot')
        raise
