"""
pytest configuration for the cara_template smoke tests.

The workspace root has its own utils/ package that shadows cara_template/utils/.
This conftest uses a session-scoped autouse fixture (NOT pytest_configure) so that
path manipulation is scoped to cara_template/tests/ only and does not interfere
with root test suites when both are run in the same pytest session.

The fixture:
  1. Saves the original sys.path, CWD, and utils-related sys.modules entries.
  2. Moves cara_template/ to sys.path[0] so bare 'utils.*' imports resolve here.
  3. Changes CWD to cara_template/ so relative config file paths resolve.
  4. Clears any stale 'utils' module cache and pre-warms from cara_template/.
  5. Restores everything at teardown so root tests see the original state.
"""

import importlib
import os
import sys

import pytest

TEMPLATE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def _cara_template_path_setup():
    original_path = sys.path[:]
    original_cwd = os.getcwd()
    original_utils = {k: v for k, v in sys.modules.items()
                      if k == "utils" or k.startswith("utils.")}

    while TEMPLATE_DIR in sys.path:
        sys.path.remove(TEMPLATE_DIR)
    sys.path.insert(0, TEMPLATE_DIR)
    os.chdir(TEMPLATE_DIR)

    for key in list(sys.modules.keys()):
        if key == "utils" or key.startswith("utils."):
            del sys.modules[key]

    importlib.import_module("utils.domains.base_domain")

    yield

    sys.path[:] = original_path
    os.chdir(original_cwd)
    for key in list(sys.modules.keys()):
        if key == "utils" or key.startswith("utils."):
            del sys.modules[key]
    sys.modules.update(original_utils)
