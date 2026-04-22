# CARA - Comprehensive Automated Risk Assessment

## Overview
CARA is a comprehensive geospatial health and emergency preparedness risk assessment platform specifically designed for Wisconsin public health departments. The application serves 95 jurisdictions including 84 public health agencies, 11 Tribal health centers, and 72 counties.

## Purpose
This tool helps public health officials:
- Evaluate multiple risk types across their jurisdictions
- Make informed preparedness decisions based on real data
- Generate comprehensive action plans
- Export data for use with industry-standard tools (Kaiser Permanente HVA)
- Monitor and analyze feedback from users

## Key Features

### Risk Assessment Types
- **Natural Hazards**: Flood, tornado, winter storm risks
- **Infectious Disease Risk**: Based on vaccination rates and population density
- **Active Shooter Risk**: Calculated using Gun Violence Archive data and NCES school safety data
- **Climate-Adjusted Risk**: Long-term climate projections
- **Social Vulnerability Index**: CDC SVI integration

### Geographic Coverage
- **County-level**: All 72 Wisconsin counties
- **Public Health Departments**: 84 local health agencies
- **Tribal Health Centers**: 11 federally recognized tribal jurisdictions
- **HERC Regions**: 6 Hospital Emergency Readiness Coalition regions
- **WEM Regions**: Wisconsin Emergency Management regions

### Data Integration
- County-specific census data from local CSV files for enhanced accuracy
- Strategic planning data with extended cache periods
- Gun Violence Archive for active shooter risk
- CDC Social Vulnerability Index
- NCES School Survey on Crime and Safety data
- Wisconsin Emergency Management data
- Hospital Emergency Readiness Coalition data

## Technical Architecture

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL with PostGIS for geospatial data
- **Data Processing**: Pandas, NumPy, GeoPandas
- **Mapping**: Folium for interactive maps
- **Scheduling**: APScheduler for automated data refreshes

### Frontend
- **Templates**: Jinja2 with Bootstrap for responsive design
- **Visualization**: Chart.js for risk distribution charts
- **Maps**: Leaflet.js integration
- **Styling**: Bootstrap with custom CARA branding

### Security
- Environment-based configuration
- Input validation and sanitization
- Secure database connections
- Rate limiting for API endpoints

## File Structure

### Core Application Files
- `app.py` - Main Flask application with all routes and logic
- `main.py` - Application entry point
- `models.py` - Database models and data structures

### Utilities (`/utils/`)
- `risk_calculation.py` - Core risk calculation algorithms
- `data_processor.py` - Data ingestion and processing
- `geo_data.py` - Geospatial data handling
- `report_generator.py` - PDF report generation
- `email_notifications.py` - Feedback notification system
- `data_refresh_scheduler.py` - Automated data updates

### Templates (`/templates/`)
- `index.html` - Main application interface
- `dashboard.html` - Jurisdiction-specific dashboards
- `methodology.html` - Risk assessment methodology
- `action_plan.html` - Preparedness action plans
- `feedback_dashboard.html` - Admin feedback monitoring

### Static Assets (`/static/`)
- CSS files for styling and accessibility
- JavaScript files for interactivity and performance
- Images and icons

### Data (`/data/`)
- Regional boundary files (GeoJSON)
- Configuration files
- Cached data and feedback logs

## Key Capabilities

### Risk Assessment
- Multi-factor risk scoring (0-1 scale)
- Weighted risk calculations based on jurisdiction type
- Historical trend analysis
- Predictive modeling capabilities

### Visualization
- Interactive choropleth maps
- Risk distribution charts
- Regional comparison dashboards
- Print-friendly summary reports

### Action Planning
- Customized preparedness recommendations
- Risk-specific mitigation strategies
- Resource allocation guidance
- Timeline-based implementation plans

### Regional Integration
- HERC region aggregation and analysis
- Kaiser Permanente HVA export format
- Multi-jurisdiction comparison tools
- Regional coordination features

### Feedback System
- User feedback collection
- Admin monitoring dashboards
- Notification system for new submissions
- Categorization and analysis tools

## Data Sources

### Government APIs
- County-specific CSV files for accurate demographic data (mobile homes, population aged 65 and older)
- Strategic planning data sources with extended cache periods
- CDC Social Vulnerability Index
- Wisconsin Emergency Management data

### Static Datasets
- Gun Violence Archive mass shooting data
- NCES School Survey on Crime and Safety
- FEMA National Risk Index
- Wisconsin tribal boundary data
- Hospital Emergency Readiness Coalition regions

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `AIRNOW_API_KEY` - EPA AirNow API for air quality data (optional)
- Local CSV files provide census demographic data with no API required
- `SESSION_SECRET` - Flask session security
- `OPENAI_API_KEY` - AI feedback analysis (optional)

### Scheduler Configuration
Located in `data/config/scheduler_config.json`, controls:
- Data refresh intervals
- API rate limits
- Cache management
- Error handling

## Deployment Requirements

### System Dependencies
- Python 3.11+
- PostgreSQL with PostGIS extension
- Gunicorn WSGI server
- Required Python packages (see pyproject.toml)

### Resource Requirements
- Minimum 2GB RAM
- 10GB storage for data and maps
- Reliable internet connection for API access
- SSL certificate for production deployment

## Usage Instructions

### For Public Health Officials
1. Navigate to the main application interface
2. Select your jurisdiction from the interactive map
3. Review risk assessment results and trends
4. Generate action plans and reports
5. Export data for integration with other tools

### For Administrators
1. Access admin dashboards via `/admin/` URLs
2. Monitor user feedback and system health
3. Review data refresh status and logs
4. Manage jurisdiction configurations
5. Generate regional reports and exports

## Support and Documentation

### User Guides
- Quick Start Guide: `/docs/quick-start`
- FAQ: `/docs/faq`
- Methodology: `/methodology`

### Technical Documentation
- API endpoints documented in code comments
- Database schema in models.py
- Configuration options in respective config files

## Security Considerations
- All API keys stored as environment variables
- Input validation on all user inputs
- Rate limiting on API endpoints
- Secure session management
- Admin interfaces protected by hidden URLs

## Compliance
- Designed to support CDC PHEP Cooperative Agreement 2024-2028
- Compatible with Kaiser Permanente HVA format
- Follows Wisconsin Emergency Management standards
- Implements public health emergency preparedness best practices

This application represents a comprehensive solution for public health preparedness planning, combining real-time data integration with advanced risk modeling to support evidence-based decision making across Wisconsin's diverse public health landscape.