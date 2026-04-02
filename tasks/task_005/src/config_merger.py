def deep_merge(base, override):
    """Recursively merge two dictionaries.

    Values in *override* take precedence over values in *base*.
    When both base and override have a dict at the same key, the dicts
    should be merged recursively rather than the override replacing the
    base entirely.

    Returns a new dictionary (does not mutate the inputs).
    """
    result = base.copy()
    # BUG: shallow update — nested dicts in override completely replace
    # nested dicts in base instead of being merged recursively
    result.update(override)
    return result
