# Task 037: Bytecode VM Stack Frame Corruption

## Description

A stack-based virtual machine implements function calls using stack frames with a base
pointer (frame pointer) and stack pointer. The RET instruction restores the stack pointer
but fails to restore the base pointer, causing local variable access in the calling
function to read from wrong stack locations after a CALL/RET sequence.

## Bug

The RET instruction pops the return value and restores SP, but does not restore BP
(base pointer / frame pointer) from the saved frame. This means after returning from
a function call, LOAD and STORE instructions in the caller use the wrong base offset,
corrupting local variable access.

## Expected Behavior

RET should restore both SP and BP from the saved call frame, so the calling function's
local variables remain accessible at their correct offsets.
