## US Connector Stubs

This directory contains placeholder connectors intended for a future fork that
targets `profile == "us_state"` in `config/jurisdiction.yaml`. The active Libya
deployment never instantiates them; they are retained as a coherent skeleton
alongside the wider `us_state` plumbing elsewhere in the codebase
(`core.py`, `utils/domains/*`, `config/risk_weights.yaml`).

Stubs currently in this directory (each returns `"Stub not implemented"` from
`fetch()` until you wire it up):

- `airnow_connector.py` — EPA AirNow API (requires `AIRNOW_API_KEY`)
- `nws_connector.py` — NOAA NWS forecasts / alerts (keyless)
- `open_fema_connector.py` — OpenFEMA Disaster Declarations, NFIP Claims, HMA Projects (keyless)
- `cdc_nssp_connector.py` — CDC NSSP ED visit surveillance (keyless)

Each connector should implement the `BaseConnector` interface:

```python
class MyConnector(BaseConnector):
    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]: ...
    def is_available(self) -> bool: ...
    def source_info(self) -> Dict[str, str]: ...
```

See `utils/connectors/base_connector.py` for the full interface and
`docs/adding_custom_connector.md` for a step-by-step guide. The endpoint URL
to implement against is documented in each stub's own module docstring.
