"""
Stack-based bytecode virtual machine.

Supports arithmetic operations, local variables via frame-relative addressing,
function calls with stack frames, and conditional/unconditional jumps.
"""

from enum import IntEnum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


class OpCode(IntEnum):
    PUSH = 0
    POP = 1
    ADD = 2
    SUB = 3
    MUL = 4
    DIV = 5
    MOD = 6
    NEG = 7
    EQ = 8
    NEQ = 9
    LT = 10
    GT = 11
    LTE = 12
    GTE = 13
    AND = 14
    OR = 15
    NOT = 16
    LOAD = 17       # Load local variable (offset from BP)
    STORE = 18      # Store local variable (offset from BP)
    GLOAD = 19      # Load global variable
    GSTORE = 20     # Store global variable
    CALL = 21       # Call function: operand = address, next byte = num_args
    RET = 22        # Return from function
    JMP = 23        # Unconditional jump
    JZ = 24         # Jump if zero
    JNZ = 25        # Jump if not zero
    DUP = 26        # Duplicate top of stack
    SWAP = 27       # Swap top two values
    PRINT = 28      # Print top of stack
    HALT = 29       # Stop execution
    NOP = 30        # No operation
    ALLOC = 31      # Allocate N local slots


@dataclass
class CallFrame:
    return_address: int
    saved_bp: int
    saved_sp: int
    num_args: int


class VMError(Exception):
    pass


class VM:
    """Stack-based virtual machine with function call support."""

    STACK_SIZE = 4096

    def __init__(self):
        self.stack: List[int] = [0] * self.STACK_SIZE
        self.sp: int = 0      # Stack pointer (points to next free slot)
        self.bp: int = 0      # Base pointer (frame pointer)
        self.ip: int = 0      # Instruction pointer
        self.globals: Dict[int, int] = {}
        self.call_stack: List[CallFrame] = []
        self.program: List[int] = []
        self.output: List[int] = []
        self.halted: bool = False
        self.max_steps: int = 100000

    def load_program(self, program: List[int]):
        self.program = program
        self.ip = 0
        self.sp = 0
        self.bp = 0
        self.halted = False
        self.call_stack = []
        self.output = []
        self.globals = {}

    def _push(self, value: int):
        if self.sp >= self.STACK_SIZE:
            raise VMError("Stack overflow")
        self.stack[self.sp] = value
        self.sp += 1

    def _pop(self) -> int:
        if self.sp <= 0:
            raise VMError("Stack underflow")
        self.sp -= 1
        return self.stack[self.sp]

    def _peek(self, offset: int = 0) -> int:
        idx = self.sp - 1 - offset
        if idx < 0:
            raise VMError("Stack underflow on peek")
        return self.stack[idx]

    def _fetch(self) -> int:
        if self.ip >= len(self.program):
            raise VMError(f"IP out of bounds: {self.ip}")
        val = self.program[self.ip]
        self.ip += 1
        return val

    def _execute_arithmetic(self, opcode: int):
        if opcode == OpCode.NEG:
            a = self._pop()
            self._push(-a)
            return
        if opcode == OpCode.NOT:
            a = self._pop()
            self._push(1 if a == 0 else 0)
            return

        b = self._pop()
        a = self._pop()

        if opcode == OpCode.ADD:
            self._push(a + b)
        elif opcode == OpCode.SUB:
            self._push(a - b)
        elif opcode == OpCode.MUL:
            self._push(a * b)
        elif opcode == OpCode.DIV:
            if b == 0:
                raise VMError("Division by zero")
            self._push(a // b)
        elif opcode == OpCode.MOD:
            if b == 0:
                raise VMError("Modulo by zero")
            self._push(a % b)
        elif opcode == OpCode.EQ:
            self._push(1 if a == b else 0)
        elif opcode == OpCode.NEQ:
            self._push(1 if a != b else 0)
        elif opcode == OpCode.LT:
            self._push(1 if a < b else 0)
        elif opcode == OpCode.GT:
            self._push(1 if a > b else 0)
        elif opcode == OpCode.LTE:
            self._push(1 if a <= b else 0)
        elif opcode == OpCode.GTE:
            self._push(1 if a >= b else 0)
        elif opcode == OpCode.AND:
            self._push(1 if (a and b) else 0)
        elif opcode == OpCode.OR:
            self._push(1 if (a or b) else 0)

    def _execute_call(self):
        addr = self._fetch()
        num_args = self._fetch()

        frame = CallFrame(
            return_address=self.ip,
            saved_bp=self.bp,
            saved_sp=self.sp - num_args,
            num_args=num_args,
        )
        self.call_stack.append(frame)

        self.bp = self.sp - num_args
        self.ip = addr

    def _execute_ret(self):
        if not self.call_stack:
            raise VMError("RET with empty call stack")

        return_value = self._pop()
        frame = self.call_stack.pop()

        self.sp = frame.saved_sp
        self.ip = frame.return_address

        self._push(return_value)

    def step(self) -> bool:
        if self.halted or self.ip >= len(self.program):
            return False

        opcode = self._fetch()

        if opcode == OpCode.HALT:
            self.halted = True
            return False

        if opcode == OpCode.NOP:
            return True

        if opcode == OpCode.PUSH:
            val = self._fetch()
            self._push(val)

        elif opcode == OpCode.POP:
            self._pop()

        elif opcode == OpCode.DUP:
            val = self._peek()
            self._push(val)

        elif opcode == OpCode.SWAP:
            a = self._pop()
            b = self._pop()
            self._push(a)
            self._push(b)

        elif opcode in (OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV,
                        OpCode.MOD, OpCode.EQ, OpCode.NEQ, OpCode.LT,
                        OpCode.GT, OpCode.LTE, OpCode.GTE, OpCode.AND,
                        OpCode.OR, OpCode.NEG, OpCode.NOT):
            self._execute_arithmetic(opcode)

        elif opcode == OpCode.LOAD:
            offset = self._fetch()
            idx = self.bp + offset
            if idx < 0 or idx >= self.STACK_SIZE:
                raise VMError(f"LOAD: invalid index {idx}")
            self._push(self.stack[idx])

        elif opcode == OpCode.STORE:
            offset = self._fetch()
            value = self._pop()
            idx = self.bp + offset
            if idx < 0 or idx >= self.STACK_SIZE:
                raise VMError(f"STORE: invalid index {idx}")
            self.stack[idx] = value

        elif opcode == OpCode.GLOAD:
            addr = self._fetch()
            self._push(self.globals.get(addr, 0))

        elif opcode == OpCode.GSTORE:
            addr = self._fetch()
            value = self._pop()
            self.globals[addr] = value

        elif opcode == OpCode.CALL:
            self._execute_call()

        elif opcode == OpCode.RET:
            self._execute_ret()

        elif opcode == OpCode.JMP:
            addr = self._fetch()
            self.ip = addr

        elif opcode == OpCode.JZ:
            addr = self._fetch()
            cond = self._pop()
            if cond == 0:
                self.ip = addr

        elif opcode == OpCode.JNZ:
            addr = self._fetch()
            cond = self._pop()
            if cond != 0:
                self.ip = addr

        elif opcode == OpCode.PRINT:
            val = self._pop()
            self.output.append(val)

        elif opcode == OpCode.ALLOC:
            n = self._fetch()
            for _ in range(n):
                self._push(0)

        else:
            raise VMError(f"Unknown opcode: {opcode}")

        return True

    def run(self) -> List[int]:
        steps = 0
        while self.step():
            steps += 1
            if steps > self.max_steps:
                raise VMError("Exceeded maximum step count")
        return self.output


class Assembler:
    """Simple assembler that converts mnemonics to bytecode."""

    def __init__(self):
        self.labels: Dict[str, int] = {}
        self.code: List[int] = []
        self.fixups: List[Tuple[int, str]] = []

    def label(self, name: str):
        self.labels[name] = len(self.code)

    def emit(self, opcode: OpCode, *args: int):
        self.code.append(int(opcode))
        for a in args:
            self.code.append(a)

    def emit_jmp(self, opcode: OpCode, label: str):
        self.code.append(int(opcode))
        self.fixups.append((len(self.code), label))
        self.code.append(0)

    def emit_call(self, label: str, num_args: int):
        self.code.append(int(OpCode.CALL))
        self.fixups.append((len(self.code), label))
        self.code.append(0)
        self.code.append(num_args)

    def assemble(self) -> List[int]:
        for pos, label_name in self.fixups:
            if label_name not in self.labels:
                raise VMError(f"Undefined label: {label_name}")
            self.code[pos] = self.labels[label_name]
        return self.code
