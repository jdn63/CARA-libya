# cara_template tests

## Running the smoke test

**From inside `cara_template/` (standalone):**

```bash
cd cara_template
python tests/smoke_test.py
```

**With pytest from the workspace root:**

```bash
pytest cara_template/tests/smoke_test.py -v
```

Both modes run 13 tests covering all 7 risk domains, the PHRAT pipeline, and the
data_processor orchestration path using synthetic connector data (no network calls,
no database required).

---

## Why conftest.py modifies `sys.path` and `sys.modules`

The workspace root (`/home/runner/workspace/`) has its own `utils/` package (the
main CARA application's utilities). `cara_template/` also has a `utils/` package
(the template's domain modules, risk engine, etc.). These two `utils` packages are
distinct and incompatible.

When pytest is invoked from the workspace root, it inserts the workspace root at
`sys.path[0]`. This causes Python to resolve `import utils` to the workspace-root
`utils/` package, which has no `domains/` sub-package, breaking all domain imports.

`conftest.py` uses a session-scoped `autouse` fixture (NOT the global
`pytest_configure` hook, which would affect root tests) to:

1. **Move `cara_template/` to `sys.path[0]`** so that bare `utils.*` imports
   resolve to `cara_template/utils/` rather than the workspace-root `utils/`.

2. **Change CWD to `cara_template/`** so that relative file paths used by
   `load_weights()` and `load_jurisdiction_config()` (e.g. `config/risk_weights.yaml`)
   resolve correctly from wherever pytest is launched.

3. **Pre-warm the `utils` module cache** by importing `utils.domains.base_domain`
   immediately after fixing `sys.path`. This ensures the correct `cara_template/utils`
   package is registered in `sys.modules` by the time any test function calls `_import()`.

4. **Restore everything at teardown**: `sys.path`, CWD, and the original `utils`
   `sys.modules` entries are all restored so root tests that run in the same session
   are unaffected.

The `_PREFIX` variable in `smoke_test.py` is computed lazily (on the first `_import()`
call inside a test function, not at module import time). This ensures the fixture
has already run before the prefix resolution attempt.

These steps are confined to `cara_template/tests/conftest.py`'s autouse fixture
scope and do not affect root test execution.
