import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.argument import Argument, Namespace, ParseError
from src.command import Command, SubCommand
from src.parser import ArgumentParser
from src.help_formatter import HelpFormatter


# ── pass-to-pass: Argument and Namespace basics ──────────────────────


class TestArgumentBasic:
    def test_argument_creation(self):
        arg = Argument(name="file", is_positional=True, help="Input file")
        assert arg.name == "file"
        assert arg.is_positional is True

    def test_argument_long_flag(self):
        arg = Argument(name="output")
        assert arg.long_flag == "--output"

    def test_argument_display_name_positional(self):
        arg = Argument(name="file", is_positional=True)
        assert arg.display_name == "file"

    def test_argument_display_name_optional(self):
        arg = Argument(name="output", short="-o")
        assert "-o" in arg.display_name
        assert "--output" in arg.display_name

    def test_argument_defaults(self):
        arg = Argument(name="x")
        assert arg.arg_type is str
        assert arg.required is False
        assert arg.default is None
        assert arg.is_flag is False


class TestNamespaceBasic:
    def test_namespace_creation(self):
        ns = Namespace(name="Alice", age=30)
        assert ns.name == "Alice"
        assert ns.age == 30

    def test_namespace_equality(self):
        ns1 = Namespace(x=1, y=2)
        ns2 = Namespace(x=1, y=2)
        assert ns1 == ns2

    def test_namespace_to_dict(self):
        ns = Namespace(a=1, b="two")
        assert ns.to_dict() == {"a": 1, "b": "two"}

    def test_namespace_repr(self):
        ns = Namespace(x=1)
        assert "x=1" in repr(ns)


class TestCommandBasic:
    def test_command_creation(self):
        cmd = Command(name="build", description="Build the project")
        assert cmd.name == "build"
        assert cmd.description == "Build the project"

    def test_add_argument(self):
        cmd = Command(name="test")
        cmd.add_argument("file", is_positional=True)
        assert len(cmd.arguments) == 1

    def test_add_subcommand(self):
        parent = Command(name="git")
        child = SubCommand(name="commit", description="Commit changes")
        parent.add_subcommand("commit", child)
        assert "commit" in parent.subcommands

    def test_positional_vs_optional(self):
        cmd = Command(name="test")
        cmd.add_argument("file", is_positional=True)
        cmd.add_argument("output", short="-o")
        assert len(cmd.positional_args) == 1
        assert len(cmd.optional_args) == 1


# ── fail-to-pass: Parser implementation ──────────────────────────


class TestParsePositional:
    @pytest.mark.fail_to_pass
    def test_single_positional(self):
        """Parse a single positional argument."""
        parser = ArgumentParser()
        parser.add_argument("filename", is_positional=True)
        result = parser.parse(["input.txt"])
        assert result.filename == "input.txt"

    @pytest.mark.fail_to_pass
    def test_multiple_positional(self):
        """Parse multiple positional arguments in order."""
        parser = ArgumentParser()
        parser.add_argument("src", is_positional=True)
        parser.add_argument("dest", is_positional=True)
        result = parser.parse(["a.txt", "b.txt"])
        assert result.src == "a.txt"
        assert result.dest == "b.txt"

    @pytest.mark.fail_to_pass
    def test_missing_required_positional_raises(self):
        """Missing required positional should raise ParseError."""
        parser = ArgumentParser()
        parser.add_argument("filename", is_positional=True, required=True)
        with pytest.raises(ParseError):
            parser.parse([])


class TestParseOptional:
    @pytest.mark.fail_to_pass
    def test_long_flag_with_value(self):
        """Parse --name value."""
        parser = ArgumentParser()
        parser.add_argument("name", help="Name")
        result = parser.parse(["--name", "Alice"])
        assert result.name == "Alice"

    @pytest.mark.fail_to_pass
    def test_short_flag_with_value(self):
        """Parse -n value."""
        parser = ArgumentParser()
        parser.add_argument("name", short="-n")
        result = parser.parse(["-n", "Bob"])
        assert result.name == "Bob"

    @pytest.mark.fail_to_pass
    def test_boolean_flag(self):
        """Parse --verbose as boolean flag."""
        parser = ArgumentParser()
        parser.add_argument("verbose", short="-v", is_flag=True)
        result = parser.parse(["--verbose"])
        assert result.verbose is True

    @pytest.mark.fail_to_pass
    def test_boolean_flag_absent_is_false(self):
        """Missing boolean flag defaults to False."""
        parser = ArgumentParser()
        parser.add_argument("verbose", short="-v", is_flag=True, default=False)
        result = parser.parse([])
        assert result.verbose is False

    @pytest.mark.fail_to_pass
    def test_default_value(self):
        """Optional with default value."""
        parser = ArgumentParser()
        parser.add_argument("output", default="out.txt")
        result = parser.parse([])
        assert result.output == "out.txt"

    @pytest.mark.fail_to_pass
    def test_required_optional_missing_raises(self):
        """Required optional arg missing should raise ParseError."""
        parser = ArgumentParser()
        parser.add_argument("config", required=True)
        with pytest.raises(ParseError):
            parser.parse([])


class TestTypeCoercion:
    @pytest.mark.fail_to_pass
    def test_int_coercion(self):
        """arg_type=int should coerce to int."""
        parser = ArgumentParser()
        parser.add_argument("count", short="-c", arg_type=int)
        result = parser.parse(["-c", "42"])
        assert result.count == 42
        assert isinstance(result.count, int)

    @pytest.mark.fail_to_pass
    def test_float_coercion(self):
        """arg_type=float should coerce to float."""
        parser = ArgumentParser()
        parser.add_argument("rate", arg_type=float)
        result = parser.parse(["--rate", "3.14"])
        assert result.rate == pytest.approx(3.14)

    @pytest.mark.fail_to_pass
    def test_bad_type_raises(self):
        """Invalid type coercion should raise ParseError."""
        parser = ArgumentParser()
        parser.add_argument("count", arg_type=int)
        with pytest.raises(ParseError):
            parser.parse(["--count", "not_a_number"])


class TestSubcommands:
    @pytest.mark.fail_to_pass
    def test_basic_subcommand(self):
        """Parse a subcommand with its own arguments."""
        parser = ArgumentParser(prog="git")
        commit = SubCommand(name="commit", description="Commit changes")
        commit.add_argument("message", short="-m", required=True)
        parser.add_subcommand("commit", commit)
        result = parser.parse(["commit", "-m", "initial commit"])
        assert result.command == "commit"
        assert result.message == "initial commit"

    @pytest.mark.fail_to_pass
    def test_subcommand_with_flag(self):
        """Subcommand with a boolean flag."""
        parser = ArgumentParser(prog="tool")
        build = SubCommand(name="build")
        build.add_argument("release", short="-r", is_flag=True, default=False)
        parser.add_subcommand("build", build)
        result = parser.parse(["build", "--release"])
        assert result.command == "build"
        assert result.release is True

    @pytest.mark.fail_to_pass
    def test_subcommand_with_positional(self):
        """Subcommand with positional argument."""
        parser = ArgumentParser(prog="tool")
        run = SubCommand(name="run")
        run.add_argument("script", is_positional=True)
        parser.add_subcommand("run", run)
        result = parser.parse(["run", "deploy.py"])
        assert result.command == "run"
        assert result.script == "deploy.py"

    @pytest.mark.fail_to_pass
    def test_unknown_subcommand_raises(self):
        """Unknown subcommand should raise ParseError."""
        parser = ArgumentParser(prog="tool")
        parser.add_subcommand("build", SubCommand(name="build"))
        with pytest.raises(ParseError):
            parser.parse(["deploy"])


class TestMixedArgs:
    @pytest.mark.fail_to_pass
    def test_positional_and_optional_mixed(self):
        """Positional and optional args can be mixed."""
        parser = ArgumentParser()
        parser.add_argument("file", is_positional=True)
        parser.add_argument("output", short="-o", default="out.txt")
        parser.add_argument("verbose", short="-v", is_flag=True, default=False)
        result = parser.parse(["input.txt", "-o", "result.txt", "--verbose"])
        assert result.file == "input.txt"
        assert result.output == "result.txt"
        assert result.verbose is True


class TestHelpFormatter:
    @pytest.mark.fail_to_pass
    def test_help_contains_description(self):
        """Help text should include the command description."""
        parser = ArgumentParser(description="A test tool", prog="mytool")
        parser.add_argument("file", is_positional=True, help="Input file")
        parser.add_argument("verbose", short="-v", is_flag=True, help="Verbose mode")
        help_text = parser.format_help()
        assert "A test tool" in help_text
        assert "file" in help_text.lower()
        assert "verbose" in help_text.lower()

    @pytest.mark.fail_to_pass
    def test_help_contains_subcommands(self):
        """Help text should list subcommands."""
        parser = ArgumentParser(description="Tool", prog="tool")
        parser.add_subcommand("build", SubCommand(name="build", description="Build project"))
        parser.add_subcommand("test", SubCommand(name="test", description="Run tests"))
        help_text = parser.format_help()
        assert "build" in help_text
        assert "test" in help_text
