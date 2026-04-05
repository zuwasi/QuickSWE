# Task 024: Plugin Loader Dependency Resolution Bug

## Problem

A plugin loader system resolves dependencies in the wrong order, causing plugins
to be initialized before their dependencies are ready. The topological sort
implementation iterates in the wrong direction, producing a reversed load order
where dependents are loaded before their dependencies.

## Expected Behavior

If plugin A depends on plugin B, then B must be loaded before A. The loader
should perform a correct topological sort so all dependencies are initialized
first.

## Files

- `src/plugin_loader.py` — Plugin registration and dependency resolution system
