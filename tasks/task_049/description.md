# Feature Request: CLI Argument Parser with Subcommands

## Summary

Build a CLI argument parser supporting positional args, optional flags (`--name value`, `--flag`), short flags (`-n value`, `-f`), type coercion, required vs optional, default values, subcommands (like `git commit -m "msg"`), and auto-generated help text.

## Current State

- `src/parser.py`: `ArgumentParser` stub — `parse()` raises `NotImplementedError`.
- `src/argument.py`: `Argument` class with `name`, `type`, `required`, `default` attributes — complete.
- `src/command.py`: `Command` and `SubCommand` classes — partial (structure only).
- `src/help_formatter.py`: `HelpFormatter` stub — `format_help()` raises `NotImplementedError`.

## Requirements

### Argument Types (`src/argument.py`)
- Positional arguments: consumed in order, required by default.
- Optional arguments: prefixed with `--` (long) or `-` (short).
- Boolean flags: `--verbose` sets True, no value consumed.
- Type coercion: `int`, `float`, `str`, `bool`.
- Default values for optional arguments.
- Required optional arguments (must be provided).

### Parser (`src/parser.py`)
1. `add_argument(name, **kwargs)` — register an argument.
2. `add_subcommand(name, command)` — register a subcommand.
3. `parse(args: list[str]) -> Namespace` — parse argument list.
4. `Namespace` object with attribute access for parsed values.
5. Raise `ParseError` for: missing required args, wrong type, unknown args.

### SubCommands (`src/command.py`)
- `Command` has its own arguments and optional subcommands.
- `SubCommand` inherits from `Command`.
- When a subcommand is used, its arguments are parsed after the subcommand name.
- Example: `["commit", "-m", "message"]` parses `commit` subcommand with `-m` flag.

### Help Formatter (`src/help_formatter.py`)
- Generate help text showing: program description, usage line, positional args, optional args, subcommands.
- Format: aligned columns with descriptions.

## Edge Cases
- `--` stops flag parsing (rest are positional).
- `-abc` is NOT treated as combined short flags (keep it simple: `-a value`).
- Boolean `--flag` vs `--no-flag` not required.
- Empty args list with required positional should error.
