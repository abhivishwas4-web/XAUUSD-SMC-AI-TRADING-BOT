"""Command registration utilities for Telegram bot."""

from typing import Callable, Dict, Any


class CommandRegistry:
    """Registry for bot commands."""

    def __init__(self):
        self.commands: Dict[str, Callable] = {}

    def register(self, name: str, handler: Callable) -> None:
        """Register a command handler."""
        self.commands[name] = handler

    def get(self, name: str) -> Callable:
        """Get a registered command handler."""
        if name not in self.commands:
            raise ValueError(f"Unknown command: {name}")
        return self.commands[name]

    def list_commands(self) -> Dict[str, str]:
        """List all registered commands with descriptions."""
        return {
            'start': 'Show bot information and capabilities',
            'help': 'Show available commands',
            'market': 'Display XAU/USD market status',
            'status': 'Display bot and provider status',
            'analyze': 'Run complete SMC analysis',
        }
