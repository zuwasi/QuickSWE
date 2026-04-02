"""CLI argument parser."""

from .argument import Argument, Namespace, ParseError
from .command import Command


class ArgumentParser:
    """CLI argument parser with subcommand support.

    Usage:
        parser = ArgumentParser(description="My tool")
        parser.add_argument("filename", is_positional=True, help="Input file")
        parser.add_argument("output", short="-o", default="out.txt", help="Output file")
        parser.add_argument("verbose", short="-v", is_flag=True, help="Verbose mode")

        result = parser.parse(["input.txt", "-o", "result.txt", "--verbose"])
        # result.filename == "input.txt"
        # result.output == "result.txt"
        # result.verbose == True
    """

    def __init__(self, description: str = "", prog: str = ""):
        self._root_command = Command(name=prog or "program", description=description)
        self._description = description
        self._prog = prog

    def add_argument(self, name: str, **kwargs) -> "ArgumentParser":
        """Add an argument to the root command.

        Args:
            name: Argument name.
            **kwargs: short, arg_type, required, default, is_flag, is_positional, help.

        Returns:
            self for chaining.
        """
        self._root_command.add_argument(name, **kwargs)
        return self

    def add_subcommand(self, name: str, command: Command) -> "ArgumentParser":
        """Register a subcommand.

        Args:
            name: Subcommand name.
            command: Command object.

        Returns:
            self for chaining.
        """
        self._root_command.add_subcommand(name, command)
        return self

    def parse(self, args: list[str]) -> Namespace:
        """Parse a list of argument strings.

        Args:
            args: List of CLI argument strings (like sys.argv[1:]).

        Returns:
            Namespace with parsed values.

        Raises:
            ParseError: If parsing fails (missing required, bad type, etc).
        """
        raise NotImplementedError("ArgumentParser.parse not yet implemented")

    def format_help(self) -> str:
        """Generate help text for this parser.

        Returns:
            Formatted help string.
        """
        raise NotImplementedError("ArgumentParser.format_help not yet implemented")

    @property
    def root_command(self) -> Command:
        return self._root_command
