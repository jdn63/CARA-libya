"""
US-specific connector stubs for the CARA template.

These are placeholder adapters retained for any future fork that targets
profile == "us_state" in config/jurisdiction.yaml. The active Libya
deployment never instantiates them; they exist as a coherent skeleton
alongside the wider us_state plumbing in core.py, utils/domains/*, and
config/risk_weights.yaml.

Available stubs (each currently returns "Stub not implemented"):
    airnow_connector.AirNowConnector    — EPA AirNow (requires AIRNOW_API_KEY)
    nws_connector.NWSConnector          — NOAA NWS heat / alerts (keyless)
    open_fema_connector.OpenFEMAConnector — OpenFEMA declarations / NFIP / HMA (keyless)
    cdc_nssp_connector.CDCNSSPConnector — CDC NSSP ED visits (keyless)

To activate a US connector in a fork:
1. Implement its fetch() method against the public API documented in the
   connector's own module docstring.
2. Add a config/profiles/us_state.yaml file that lists the connector name
   under connectors:.
3. Register any required environment variables in .env.example.
"""
