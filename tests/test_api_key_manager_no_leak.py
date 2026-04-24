"""Regression test for the APIKeyManager.validate_key outer exception handler.

Locks in the contract that the outer ``except`` block in
``APIKeyManager.validate_key`` never leaks the configured API key into
either the returned status tuple or into log records, for every exception
type the handler catches (``requests.exceptions.RequestException``,
``ValueError``, ``KeyError``, ``TypeError``).

This protects the existing fixes for CodeQL ``py/clear-text-logging-
sensitive-data`` alerts #8, #14, and #15 from silently regressing if
someone later "simplifies" the literal-string dispatch back to
``type(e).__name__`` or starts logging ``str(e)`` directly.
"""

import logging

import pytest
import requests

from utils import api_key_manager as akm


SECRET_KEY = "SECRET_TEST_KEY_abcdef0123456789_DO_NOT_LEAK"

EXCEPTION_CASES = [
    (
        requests.exceptions.RequestException(
            f"connection failed for https://api.example/?key={SECRET_KEY}"
        ),
        "RequestException",
    ),
    (ValueError(f"unexpected payload containing {SECRET_KEY}"), "ValueError"),
    (KeyError(f"missing field near {SECRET_KEY}"), "KeyError"),
    (TypeError(f"bad type with {SECRET_KEY} in message"), "TypeError"),
]


@pytest.fixture
def manager_with_key(monkeypatch):
    """An APIKeyManager whose CENSUS_API_KEY is set to SECRET_KEY."""
    monkeypatch.setenv("CENSUS_API_KEY", SECRET_KEY)
    return akm.APIKeyManager()


@pytest.mark.parametrize("exc,expected_label", EXCEPTION_CASES)
def test_validate_key_outer_exception_does_not_leak_secret(
    monkeypatch, caplog, manager_with_key, exc, expected_label
):
    """For each caught exception type:
    - the returned status string contains the literal class label but NOT the key
    - the emitted log record contains the literal class label but NOT the key
    """
    # Force the outer handler by making the per-service inner validator raise.
    def raise_exc(_api_key):
        raise exc

    monkeypatch.setattr(manager_with_key, "_validate_census_key", raise_exc)

    caplog.set_level(logging.DEBUG)

    is_valid, status = manager_with_key.validate_key(
        "CENSUS_API_KEY", force_refresh=True
    )

    assert is_valid is False
    assert SECRET_KEY not in status, (
        f"API key leaked into returned status string: {status!r}"
    )
    assert expected_label in status, (
        f"Expected literal label {expected_label!r} missing from status: {status!r}"
    )

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert SECRET_KEY not in log_text, (
        f"API key leaked into log output:\n{log_text}"
    )
    assert expected_label in log_text, (
        f"Expected literal label {expected_label!r} missing from logs:\n{log_text}"
    )


def test_validate_key_outer_handler_uses_only_literal_labels(manager_with_key):
    """Defensive check: the four labels emitted by the dispatch are exactly
    the hard-coded set the security comment promises. If someone adds a new
    branch they must update this set (and re-justify the analyzer-friendly
    pattern), which is the whole point of the regression."""
    expected_labels = {"RequestException", "ValueError", "KeyError", "TypeError"}

    import inspect
    import re

    raw_source = inspect.getsource(akm.APIKeyManager.validate_key)
    # Strip whole-line and trailing comments so this assertion is not
    # tripped by the explanatory comment block above the dispatch (which
    # legitimately mentions the forbidden pattern by name).
    code_only_lines = []
    for line in raw_source.splitlines():
        stripped = re.sub(r"#.*$", "", line)
        if stripped.strip():
            code_only_lines.append(stripped)
    code_only = "\n".join(code_only_lines)

    for label in expected_labels:
        assert f'"{label}"' in code_only, (
            f"Outer handler is missing the literal label {label!r} — "
            "the isinstance-dispatch pattern that breaks the CodeQL "
            "taint chain may have been refactored away."
        )
    assert "type(e).__name__" not in code_only, (
        "Outer handler reintroduced type(e).__name__, which CodeQL flags "
        "as tainted. Use the literal-string isinstance dispatch instead."
    )
