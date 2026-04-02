"""Command and SubCommand for CLI parser."""

from .argument import Argument


class Command:
    """A CLI command with its own arguments and optional subcommands.

    Commands can have:
    - Positional arguments
    - Optional arguments (flags)
    - Subcommands
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._arguments: list[Argument] = []
        self._subcommands: dict[str, "Command"] = {}

    def add_argument(self, name: str, **kwargs) -> "Command":
        """Add an argument to this command.

        Args:
            name: Argument name.
            **kwargs: Passed to Argument constructor.

        Returns:
            self for chaining.
        """
        self._arguments.append(Argument(name=name, **kwargs))
        return self

    def add_subcommand(self, name: str, command: "Command") -> "Command":
        """Register a subcommand.

        Args:
            name: The subcommand name (what user types).
            command: The Command object for the subcommand.

        Returns:
            self for chaining.
        """
        self._subcommands[name] = command
        return self

    @property
    def arguments(self) -> list[Argument]:
        return list(self._arguments)

    @property
    def subcommands(self) -> dict[str, "Command"]:
        return dict(self._subcommands)

    @property
    def positional_args(self) -> list[Argument]:
        return [a for a in self._arguments if a.is_positional]

    @property
    def optional_args(self) -> list[Argument]:
        return [a for a in self._arguments if not a.is_positional]


class SubCommand(Command):
    """A subcommand — inherits from Command.

    Functionally identical to Command but semantically indicates
    it's meant to be used as a subcommand of another Command.
    """
    pass
