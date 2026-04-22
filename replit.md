# CARA - Comprehensive Automated Risk Assessment

## Overview
CARA is a geospatial health and emergency preparedness risk assessment platform for Wisconsin public health departments. It provides multi-domain risk scoring, integrates scheduled/cached data from authoritative sources, and offers actionable preparedness guidance. The platform aims to enhance emergency response and strategic planning across Wisconsin's 95 health departments, supporting 101 jurisdiction entries for county-level risk mapping.

## User Preferences
Preferred communication style: Simple, everyday language.

DOCUMENTATION FORMATTING RULES (permanent, applies to every file without exception):
- Never add icons, emoji, or decorative symbols anywhere in any file.
- Never use box-drawing or tree-drawing characters (such as the Unicode characters for vertical bars, horizontal dashes, corner connectors, or branch connectors used in directory tree diagrams). Use plain ASCII indentation or prose instead.
- Never use the multiplication sign or similar non-standard punctuation as a bullet or separator.
- Do not use decorative horizontal dividers made of repeated symbols unless they are a required part of Markdown table syntax.
- Keep all documentation, README files, guides, and analysis documents plain and professional. No decorative formatting of any kind.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python) with a modular utility structure.
- **Database**: PostgreSQL with PostGIS extension.
- **Data Processing**: Pandas, NumPy, and GeoPandas for manipulation, including Z-score normalization and outlier handling.
- **Scheduling**: APScheduler for automated data refreshes.
- **API Integration**: RESTful APIs for scheduled/cached data.
- **Configuration Management**: YAML-based configuration for risk domain weights, temporal weights, and jurisdiction-specific overrides.

### Frontend Architecture
- **Templates**: Jinja2 with Bootstrap 5 for responsive design.
- **Styling**: Custom CSS with accessibility support and a dark theme.
- **Visualization**: Folium for interactive geospatial visualizations. CSS progress bars for BSTA temporal components.
- **JavaScript**: Modern ES6+ for dynamic interactions.

### Core System Features
- **Risk Assessment Engine**: Provides multi-domain scoring (natural hazards, infectious disease, active shooter, climate-adjusted risks, dam failure, vector-borne disease) with weighted calculations and geographic scaling. Includes historical analysis, predictive modeling, and detailed logging of variable contributions.
- **Multi-Discipline Support**: Supports both Public Health and Emergency Management assessment perspectives, using the same data sources but different vulnerability/resilience weights emphasizing population health outcomes (PH) or critical infrastructure impacts (EM).
- **Data Integration Layer**: Manages scheduled/cached and static data, including geospatial data, with robust validation. All external data is pre-fetched by scheduler jobs and stored in PostgreSQL cache; no external API calls occur during user assessments.
- **User Interface Components**: Features an interactive dashboard, automated action plans, PDF report generation, and user feedback.
- **Administrative Features**: Includes scheduler management, feedback analytics, and system status monitoring.
- **UI/UX Decisions**: Utilizes Bootstrap 5 for consistent and responsive design, custom CSS for branding, and interactive mapping/charting. Includes a "Strategic Planning Mode" with adjusted temporal frameworks.
- **Technical Implementations**: Incorporates database connection pooling, centralized API key validation, comprehensive heat vulnerability assessment, and climate-adjusted risk methodologies. Supports multi-point air quality sampling.
- **Data Export**: Functionality for exporting Kaiser Permanente Hazard Vulnerability Analysis (HVA) compatible Excel reports for HERC regions and individual jurisdictions, populating specific fields based on CARA's data. Also includes a PH vs EM comparison Excel export.
- **Natural Hazard Risk Methodology**: EVR (Exposure-Vulnerability-Resilience) framework with health impact factor for natural hazards, utilizing real NOAA Storm Events counts and OpenFEMA claims/declarations.
- **Dam Failure Risk**: Standalone EVR domain using NID Wisconsin dam inventory data, with downstream population exposure computed based on inundation zones.
- **Vector-Borne Disease Risk**: Standalone domain covering Lyme disease and West Nile Virus, using real county-level incidence rates per 100k from official WI DHS EPHT CSV downloads (automated weekly refresh), environmental factors, and climate-adjusted range expansion projections.

## External Dependencies

### API Integrations
- **Local Census Data Files**: County-specific demographic and housing data from CSV files.
- **Wisconsin DHS API**: Health metrics and surveillance data.
- **WI DHS EPHT (Lyme/WNV Surveillance)**: County-level vector-borne disease incidence rates from official DHS EPHT CSV downloads (lyme-county.csv, west-nile-data-county.csv). All 72 counties, confirmed/probable case counts and crude rates per 100,000. Weekly automated CSV download. Source: WEDSS via DHS EPHT at dhs.wisconsin.gov/epht.
- **CDC/ATSDR SVI 2022 ArcGIS REST API**: County-level Social Vulnerability Index percentile rankings for all 72 Wisconsin counties. Bulk-fetched via single API call. Data stored in `data/svi/wisconsin_svi_data.json` with real RPL_THEMES values. Scheduler refreshes annually via `fetch_bulk_svi_data()`.
- **FEMA APIs**: Natural hazard risk indices.
- **OpenFEMA APIs (keyless)**: Disaster Declarations Summaries v2, NFIP Redacted Claims v2, Hazard Mitigation Assistance Projects v4.
- **NOAA NCEI Storm Events Database**: Bulk CSV downloads of Wisconsin storm events.
- **WI DNR Dam Safety Database (keyless, primary)**: Wisconsin Repository of Dams ArcGIS FeatureServer.
- **USACE NID ArcGIS FeatureServer (keyless, fallback)**: National Inventory of Dams.
- **EPA AirNow API**: Air quality monitoring.
- **NOAA/NWS**: Heat forecasting data.
- **Wisconsin Hospital Association (WHA) API**: For hospital capacity and related metrics.

### Third-Party Services
- **Bootstrap 5**: Frontend framework.
- **Font Awesome**: Icon library.