# Reference controls

The agents live in `serqet/baselines.py` so they share the tool gateway with a future model runner.

- `oracle_agent` re-checks the oracle immediately before a side effect.
- `always_refuse` declines without calling `execute_action`.
- `reckless_completer` acts and claims success.
- `cached_authority_agent` reuses the first decision.

They are not models. Pass counts belong in the "reference controls" section of the report.
