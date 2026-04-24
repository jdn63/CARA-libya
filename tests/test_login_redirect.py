"""Regression tests for the post-login redirect allow-list.

Locks in the behavior of routes.public._resolve_post_login_path so that
open-redirect tricks (CodeQL py/url-redirection alert #4) cannot reappear
through a future "small refactor" of the helper.
"""

import pytest

from routes.public import _resolve_post_login_path


SAFE_CASES = [
    ('/', '/'),
    ('/dashboard', '/dashboard'),
    ('/dashboard/LY-063', '/dashboard/LY-063'),
    ('/methodology/inform', '/methodology/inform'),
    ('/about/', '/about/'),
    ('/data-sources/who', '/data-sources/who'),
    ('/dashboard/LY-001?foo=bar', '/dashboard/LY-001'),
    ('/dashboard/LY-001#section', '/dashboard/LY-001'),
]

UNSAFE_CASES = [
    'https://evil.example/path',
    'http://evil.example/path',
    '//evil.example/path',
    '/\\evil.example/path',
    '\\\\evil.example\\path',
    'javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    '/dashboard/\nLocation: https://evil.example',
    ' /dashboard/LY-063',
    '\t/dashboard/LY-063',
    '/random/path/that/is/not/allowed',
    '/admin',
    '',
    None,
    123,
]


@pytest.mark.parametrize('raw, expected', SAFE_CASES)
def test_safe_paths_pass_through(raw, expected):
    assert _resolve_post_login_path(raw) == expected


@pytest.mark.parametrize('raw', UNSAFE_CASES)
def test_unsafe_paths_collapse_to_root(raw):
    assert _resolve_post_login_path(raw) == '/'
