import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vm import VM, OpCode, Assembler, VMError


class TestBasicVM:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_arithmetic(self):
        vm = VM()
        vm.load_program([
            OpCode.PUSH, 10,
            OpCode.PUSH, 3,
            OpCode.ADD,
            OpCode.PRINT,
            OpCode.HALT,
        ])
        output = vm.run()
        assert output == [13]

    @pytest.mark.pass_to_pass
    def test_simple_function_no_locals_in_caller(self):
        asm = Assembler()
        # Main: push 5, call double, print, halt
        asm.emit(OpCode.PUSH, 5)
        asm.emit_call("double", 1)
        asm.emit(OpCode.PRINT)
        asm.emit(OpCode.HALT)
        # double: load arg0, push 2, mul, ret
        asm.label("double")
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.PUSH, 2)
        asm.emit(OpCode.MUL)
        asm.emit(OpCode.RET)

        vm = VM()
        vm.load_program(asm.assemble())
        output = vm.run()
        assert output == [10]

    @pytest.mark.pass_to_pass
    def test_global_variables(self):
        vm = VM()
        vm.load_program([
            OpCode.PUSH, 42,
            OpCode.GSTORE, 0,
            OpCode.GLOAD, 0,
            OpCode.PRINT,
            OpCode.HALT,
        ])
        output = vm.run()
        assert output == [42]


class TestFrameRestore:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_caller_local_after_call(self):
        """Caller's local variable should be intact after function call returns."""
        asm = Assembler()
        # Main: set local x=100, call identity(7), read x, print both
        asm.emit_jmp(OpCode.JMP, "main")

        asm.label("identity")
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.RET)

        asm.label("main")
        asm.emit(OpCode.ALLOC, 2)       # allocate 2 locals: slot 0, slot 1
        asm.emit(OpCode.PUSH, 100)
        asm.emit(OpCode.STORE, 0)       # local[0] = 100
        asm.emit(OpCode.PUSH, 200)
        asm.emit(OpCode.STORE, 1)       # local[1] = 200

        asm.emit(OpCode.PUSH, 7)
        asm.emit_call("identity", 1)
        asm.emit(OpCode.PRINT)          # print return value (7)

        asm.emit(OpCode.LOAD, 0)        # load local[0] — should be 100
        asm.emit(OpCode.PRINT)
        asm.emit(OpCode.LOAD, 1)        # load local[1] — should be 200
        asm.emit(OpCode.PRINT)
        asm.emit(OpCode.HALT)

        vm = VM()
        vm.load_program(asm.assemble())
        output = vm.run()
        assert output == [7, 100, 200]

    @pytest.mark.fail_to_pass
    def test_nested_calls_preserve_frames(self):
        """Nested function calls should each restore their caller's frame."""
        asm = Assembler()
        asm.emit_jmp(OpCode.JMP, "main")

        asm.label("add_one")
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.PUSH, 1)
        asm.emit(OpCode.ADD)
        asm.emit(OpCode.RET)

        asm.label("add_two")
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.PUSH, 1)
        asm.emit(OpCode.ADD)
        asm.emit_call("add_one", 1)
        asm.emit(OpCode.RET)

        asm.label("main")
        asm.emit(OpCode.ALLOC, 1)
        asm.emit(OpCode.PUSH, 50)
        asm.emit(OpCode.STORE, 0)       # local[0] = 50

        asm.emit(OpCode.PUSH, 10)
        asm.emit_call("add_two", 1)     # add_two(10) -> 12
        asm.emit(OpCode.PRINT)

        asm.emit(OpCode.LOAD, 0)        # should still be 50
        asm.emit(OpCode.PRINT)
        asm.emit(OpCode.HALT)

        vm = VM()
        vm.load_program(asm.assemble())
        output = vm.run()
        assert output == [12, 50]

    @pytest.mark.fail_to_pass
    def test_multiple_calls_sequential(self):
        """Multiple sequential calls from same function should preserve locals."""
        asm = Assembler()
        asm.emit_jmp(OpCode.JMP, "main")

        asm.label("square")
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.MUL)
        asm.emit(OpCode.RET)

        asm.label("main")
        asm.emit(OpCode.ALLOC, 1)
        asm.emit(OpCode.PUSH, 99)
        asm.emit(OpCode.STORE, 0)

        asm.emit(OpCode.PUSH, 3)
        asm.emit_call("square", 1)
        asm.emit(OpCode.PRINT)          # 9

        asm.emit(OpCode.PUSH, 4)
        asm.emit_call("square", 1)
        asm.emit(OpCode.PRINT)          # 16

        asm.emit(OpCode.LOAD, 0)        # local[0] should still be 99
        asm.emit(OpCode.PRINT)
        asm.emit(OpCode.HALT)

        vm = VM()
        vm.load_program(asm.assemble())
        output = vm.run()
        assert output == [9, 16, 99]

    @pytest.mark.fail_to_pass
    def test_local_modified_between_calls(self):
        """Local modified between calls should retain its updated value."""
        asm = Assembler()
        asm.emit_jmp(OpCode.JMP, "main")

        asm.label("noop_fn")
        asm.emit(OpCode.PUSH, 0)
        asm.emit(OpCode.RET)

        asm.label("main")
        asm.emit(OpCode.ALLOC, 1)
        asm.emit(OpCode.PUSH, 10)
        asm.emit(OpCode.STORE, 0)       # local[0] = 10

        asm.emit(OpCode.PUSH, 0)
        asm.emit_call("noop_fn", 1)
        asm.emit(OpCode.POP)

        asm.emit(OpCode.PUSH, 20)
        asm.emit(OpCode.STORE, 0)       # local[0] = 20

        asm.emit(OpCode.PUSH, 0)
        asm.emit_call("noop_fn", 1)
        asm.emit(OpCode.POP)

        asm.emit(OpCode.LOAD, 0)        # should be 20
        asm.emit(OpCode.PRINT)
        asm.emit(OpCode.HALT)

        vm = VM()
        vm.load_program(asm.assemble())
        output = vm.run()
        assert output == [20]

    @pytest.mark.fail_to_pass
    def test_two_locals_after_call(self):
        """Multiple locals should all be correct after a function call."""
        asm = Assembler()
        asm.emit_jmp(OpCode.JMP, "main")

        asm.label("add")
        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.LOAD, 1)
        asm.emit(OpCode.ADD)
        asm.emit(OpCode.RET)

        asm.label("main")
        asm.emit(OpCode.ALLOC, 3)       # locals: slot 0, 1, 2
        asm.emit(OpCode.PUSH, 11)
        asm.emit(OpCode.STORE, 0)       # local[0] = 11
        asm.emit(OpCode.PUSH, 22)
        asm.emit(OpCode.STORE, 1)       # local[1] = 22
        asm.emit(OpCode.PUSH, 33)
        asm.emit(OpCode.STORE, 2)       # local[2] = 33

        asm.emit(OpCode.PUSH, 5)
        asm.emit(OpCode.PUSH, 6)
        asm.emit_call("add", 2)
        asm.emit(OpCode.PRINT)          # 11

        asm.emit(OpCode.LOAD, 0)
        asm.emit(OpCode.PRINT)          # should be 11
        asm.emit(OpCode.LOAD, 1)
        asm.emit(OpCode.PRINT)          # should be 22
        asm.emit(OpCode.LOAD, 2)
        asm.emit(OpCode.PRINT)          # should be 33
        asm.emit(OpCode.HALT)

        vm = VM()
        vm.load_program(asm.assemble())
        output = vm.run()
        assert output == [11, 11, 22, 33]
