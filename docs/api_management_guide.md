# Libya CARA - External API and Health Monitoring Guide

## Overview

Libya CARA fetches risk data from a small set of public humanitarian
APIs on a scheduled cadence. None of the active connectors used by
the Libya profile require an API key. This document describes:

- What external services Libya CARA depends on
- How to monitor their availability via the platform's health endpoints
- The retry and validation helpers in `utils/api_key_manager.py` for
  the optional services that do require credentials
- How to add a new optional API key safely

## 1. Active Connectors (no API key required)

The Libya profile relies entirely on public humanitarian endpoints
that do not require authentication. They are scheduled by APScheduler
and cached on disk under `data/cache/`.

| Connector | Endpoint | Auth | Schedule |
|-----------|----------|------|----------|
| OCHA HDX (CKAN) | data.humdata.org/api/3/ | none | weekly (168 h) |
| HeiGIT Accessibility | hot.storage.heigit.org | none | weekly (168 h) |
| IDMC via OCHA HDX | data.humdata.org/api/3/ | none | weekly (168 h) |
| WHO Libya via OCHA HDX | data.humdata.org/api/3/ | none | monthly (720 h) |
| WHO GHO (legacy fallback) | ghoapi.azureedge.net/api/ | none | monthly (720 h) |
| World Bank Open Data | api.worldbank.org/v2/ | none | monthly (720 h) |
| OpenAQ | api.openaq.org/v2/ | none | monthly (720 h) |

Connector registry: `utils/connector_registry.py`. Scheduler config:
`data/config/scheduler_config.json`.

File-based and manual-upload sources (EM-DAT, NCDC Libya, COI Libya,
IOM DTM fallback) are described in
`docs/data_sources_comprehensive_analysis.md`.

## 2. Optional Services that Require Credentials

Only the following service requires a credential and only when the
corresponding optional feature is enabled:

| Environment variable | Used for |
|----------------------|----------|
| `CARA_ACCESS_PASSWORD` | Session-based access gate (set this Replit secret to enable password-gating). If unset, the app runs in open development mode |
| `OPENAI_API_KEY` | Optional AI-assisted analysis; the app degrades gracefully if absent |

To set or rotate a secret in Replit, use the Secrets pane. Do not
commit credentials to source control.

## 3. Health Endpoints

### 3.1 Application Health

```
GET /health
```

Returns a small JSON document with the application status. Used by
deployment health checks. This route is exempt from authentication.

### 3.2 Connector Cache Status (operator view)

The dashboard surfaces a per-tile freshness badge that shows the
reporting year of each indicator and tags whether the value is
`local`, `measured`, `national`, `national_proxy`, or `proxy` (see
`docs/data_dictionary.md`). Operators can confirm cache health by
listing files under `data/cache/<connector>/` and checking their
modification times.

## 4. Retry Helper

`utils/api_key_manager.py` exposes a `with_retry` decorator for any
external HTTP call. It applies an exponential backoff:

```python
from utils.api_key_manager import with_retry
import requests

@with_retry(max_retries=3, base_delay=1.0, backoff_factor=2.0)
def fetch_external_data(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

Default behaviour:

- Up to 3 retry attempts after the initial call
- Delays: 1 s, 2 s, 4 s
- Errors are logged with secrets redacted before logging

## 5. Optional API Key Decorator

For optional services that require a credential, the
`@api_key_required` decorator short-circuits the call when the key is
absent:

```python
from utils.api_key_manager import api_key_required

@api_key_required('OPENAI_API_KEY')
def generate_briefing(text):
    ...
```

When the key is missing, the wrapped function returns `None` (or a
documented degraded response) instead of raising, so the dashboard can
continue to render with the rest of the indicators.

## 6. Secret Redaction in Logs

`_redact_secrets()` (in `utils/api_key_manager.py`) replaces any
occurrence of a known secret string with `***REDACTED***` before
logging or before returning an error message in a status payload.
This protects against accidental key leakage through `requests`
exception messages that embed the request URL. Closes CodeQL
`py/clear-text-logging-sensitive-data`.

## 7. Adding a New Optional API Key

1. Add the key name to `APIKeyManager.__init__` so it is loaded from
   the environment.
2. Implement the upstream call inside its own connector module under
   `utils/connectors/`, decorated with `@api_key_required` and
   `@with_retry`.
3. Register the connector in `utils/connector_registry.py`.
4. Add the connector to a scheduler job in `core.py` under the
   `CARA_PROFILE=libya` block.
5. Document the key, the upstream endpoint, and the cache path in
   `docs/data_sources_comprehensive_analysis.md` and
   `docs/data_dictionary.md`.
6. Add the key as a Replit secret in the deployment environment.

## 8. Best Practices

- Always set a short timeout (recommended: 10 seconds) on external
  HTTP calls.
- Never log API keys or full request URLs that contain query-string
  credentials. Use `_redact_secrets()` before logging when in doubt.
- Cache external responses on disk under `data/cache/<connector>/`
  so user-facing requests never block on an upstream call.
- Treat any credentialed service as optional: the dashboard must
  continue to render even if the credential is unset.
