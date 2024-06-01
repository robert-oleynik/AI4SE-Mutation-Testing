# Mutation Collector

Collects source mutations from a git repository.

## Strategies

Strategies are used to identify mutations from a git repository:

- `test_mods`: Looks for modified source code inside of `tests/` directory and a Python source file modified else where. Then identifies the modified functions and create mutation samples from these. This strategy will discard all modification, which not change the structure of the modified functions.
