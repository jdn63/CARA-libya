## US Connector Stubs

This directory contains connectors for US-specific data sources used by the `us_state` profile.

The implementations for these connectors live in the main CARA Wisconsin codebase. When adapting
the template for a US state, copy the relevant connector implementations from the Wisconsin
deployment and place them here. Each connector must implement the BaseConnector interface.

Connectors needed for the US state profile:

- `airnow_connector.py` — EPA AirNow API (requires AIRNOW_API_KEY)
- `nws_connector.py` — NWS Alerts API (no key required)
- `open_fema_connector.py` — OpenFEMA Disaster Declarations and NFIP Claims (no key required)
- `fema_nri_connector.py` — FEMA National Risk Index (static CSV from attached_assets/)
- `cdc_nssp_connector.py` — CDC NSSP ESSENCE ED visits (no key required)
- `cdc_svi_connector.py` — CDC SVI ArcGIS REST API (no key required)
- `census_connector.py` — US Census ACS (requires CENSUS_API_KEY)
- `chr_connector.py` — County Health Rankings annual CSV (no key required)
- `cdc_places_connector.py` — CDC PLACES Socrata API (no key required)
- `noaa_ncei_connector.py` — NOAA Storm Events Database (no key required)
- `wi_dnr_connector.py` — (Wisconsin-specific) WI DNR Dam Safety ArcGIS (no key required)
- `nid_connector.py` — USACE National Inventory of Dams (no key required)

Each connector should implement:

```python
class MyConnector(BaseConnector):
    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]: ...
    def is_available(self) -> bool: ...
    def source_info(self) -> Dict[str, str]: ...
```

See `utils/connectors/base_connector.py` for the full interface.
See `docs/adding_custom_connector.md` for a step-by-step guide.
