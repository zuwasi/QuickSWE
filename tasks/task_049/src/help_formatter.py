"""Help text formatter for CLI parser."""

from .command import Command


class HelpFormatter:
    """Formats help text for CLI commands.

    Generates:
    - Description
    - Usage line
    - Positional arguments section
    - Optional arguments section
    - Subcommands section
    """

    def __init__(self, indent: int = 2, col_width: int = 24):
        self._indent = indent
        self._col_width = col_width

    def format_help(self, command: Command, prog: str = "") -> str:
        """Generate formatted help text for a command.

        Args:
            command: The Command to format help for.
            prog: Program name for the usage line.

        Returns:
            Formatted help string.
        """
        raise NotImplementedError("HelpFormatter.format_help not yet implemented")

    def format_usage(self, command: Command, prog: str = "") -> str:
        """Generate a usage line.

        Args:
            command: The Command.
            prog: Program name.

        Returns:
            Usage string like "usage: prog [options] <args>".
        """
        raise NotImplementedError("HelpFormatter.format_usage not yet implemented")
