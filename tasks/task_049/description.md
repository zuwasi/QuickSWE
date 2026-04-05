# Task 049: CSP Channel Select Fairness Bug

## Description

A CSP (Communicating Sequential Processes) channel implementation provides unbuffered
and buffered channels with send/recv operations, plus a `select()` operation that
waits on multiple channels simultaneously.

## Bug

The `select()` function iterates through channels in order and always picks the first
ready channel. When multiple channels are ready, later channels are starved. The correct
behavior is to randomly choose among ready channels for fairness.

## Expected Behavior

When multiple channels are ready, `select()` should choose uniformly at random among
them, ensuring fair scheduling and preventing starvation of any channel.
