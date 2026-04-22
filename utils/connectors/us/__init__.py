"""
US-specific connector stubs for CARA template.

These connectors wrap the Wisconsin CARA data utilities for use in other
US state deployments. Each stub documents which Wisconsin source file to
adapt and what the connector expects.

Available stubs:
    airnow_connector.AirNowConnector    — EPA AirNow (requires AIRNOW_API_KEY)
    nws_connector.NWSConnector          — NOAA NWS heat forecasts (keyless)
    open_fema_connector.OpenFEMAConnector — OpenFEMA declarations/NFIP/HMA (keyless)
    cdc_nssp_connector.CDCNSSPConnector — CDC NSSP ED visits (keyless)

To activate a US connector:
1. Implement its fetch() method by adapting the Wisconsin source file noted in
   each connector's module docstring.
2. Add the connector name to config/profiles/us_state.yaml under connectors:.
3. Register any required environment variables in .env.example.
"""
