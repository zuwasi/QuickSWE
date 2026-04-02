# Task 012: Replace Magic Numbers with Named Constants

## Current State

`src/game_engine.py` implements a simple 2-D game engine with functions for player movement, collision detection, and score calculation. The code is riddled with **magic numbers** — raw numeric literals sprinkled throughout:

| Number | Meaning |
|--------|---------|
| `800`  | Screen width in pixels |
| `600`  | Screen height in pixels |
| `32`   | Tile size in pixels |
| `100`  | Maximum player health |
| `1.5`  | Speed multiplier for sprinting |

These appear multiple times across different functions. Anyone reading the code must guess what `800` means in context.

## Code Smell

- **Magic Numbers** — unnamed numeric literals that obscure intent and create a maintenance burden.

## Requested Refactoring

Define named constants at module level:

```python
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
MAX_HEALTH = 100
SPEED_MULTIPLIER = 1.5
```

Replace every occurrence of the raw number with the corresponding constant. All game functions must use these constants instead of literals.

## Acceptance Criteria

- [ ] `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `TILE_SIZE`, `MAX_HEALTH`, `SPEED_MULTIPLIER` are importable module-level attributes of `src.game_engine`.
- [ ] No magic numbers (`800`, `600`, `32`, `100`, `1.5`) remain as raw literals in the function bodies.
- [ ] All game functions continue to produce the same results.
