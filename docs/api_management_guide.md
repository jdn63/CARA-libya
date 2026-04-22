# API Management and Health Monitoring Guide

## Overview

The CARA application now includes a comprehensive API key management and health monitoring system that provides:

- Centralized API key validation
- Automatic retry logic for API failures  
- Health check endpoints for external services
- Cached validation results to reduce overhead

## API Health Check Endpoints

### 1. All Services Health Check
```
GET /health/apis
```
Returns the health status of all configured API services.

**Example Response:**
```json
{
  "overall_health": "healthy",
  "configured_services": 3,
  "total_services": 4,
  "services": {
    "AIRNOW_API_KEY": {
      "configured": true,
      "valid": true,
      "status": "AirNow API key valid",
      "last_checked": "2025-09-09T10:36:44.056163"
    },
    "FBI_CRIME_DATA_API_KEY": {
      "configured": true,
      "valid": true,
      "status": "FBI Crime Data API key valid",
      "last_checked": "2025-09-09T10:36:44.196337"
    }
  },
  "timestamp": "2025-07-05T10:36:44.429064"
}
```

### 2. Individual Service Health Check
```
GET /health/apis/<service>
```
Returns detailed health status for a specific API service.

**Example:**
```bash
curl http://localhost:5000/health/apis/AIRNOW_API_KEY
```

### 3. System Health Check
```
GET /health/system
```
Comprehensive health check including database and all API services.

**Example Response:**
```json
{
  "system_health": "healthy",
  "database": {
    "status": "healthy",
    "error": null
  },
  "api_services": {
    "configured_count": 3,
    "healthy_count": 3,
    "status": "healthy"
  },
  "timestamp": "2025-07-05T10:36:53.964986"
}
```

## Using API Management in Code

### 1. API Key Validation Decorator

Use the `@api_key_required` decorator to ensure API keys are available:

```python
from utils.api_key_manager import api_key_required

# Note: Census data now uses local CSV files for enhanced accuracy and reliability
# @api_key_required('CENSUS_API_KEY')  # No longer needed
def fetch_census_data(county_name):
    # Census data loaded from local files - no API key required
    from utils.census_data_loader import WisconsinCensusDataLoader
    # ... your API call code
```

### 2. Automatic Retry Decorator

Use the `@with_retry` decorator to add automatic retry logic:

```python
from utils.api_key_manager import with_retry
import requests

@with_retry(max_retries=3, base_delay=1.0, backoff_factor=2.0)
def fetch_external_data(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

### 3. Combined Usage

You can combine both decorators for robust API calls:

```python
from utils.api_key_manager import api_key_required, with_retry

@api_key_required('AIRNOW_API_KEY')
@with_retry(max_retries=3, base_delay=1.0, backoff_factor=2.0)
def fetch_air_quality_data(location):
    api_key = os.environ.get('AIRNOW_API_KEY')
    url = f"https://www.airnowapi.org/aq/observation/zipCode/current/?format=json&zipCode={location}&API_KEY={api_key}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

## Supported API Services

The system currently supports validation for:

1. **AIRNOW_API_KEY** - EPA AirNow API for air quality data
2. **FBI_CRIME_DATA_API_KEY** - FBI Crime Data API for active shooter risk
3. **OPENAI_API_KEY** - AI analysis (optional)
4. **OPENAI_API_KEY** - OpenAI API

## Configuration

API keys are configured via environment variables:

```bash
export AIRNOW_API_KEY="your_airnow_api_key"
# Note: Census data now uses local CSV files for enhanced accuracy
export FBI_CRIME_DATA_API_KEY="your_fbi_api_key"
export OPENAI_API_KEY="your_openai_api_key"
```

## Features

### Intelligent Caching
- API key validations are cached for 1 hour to reduce overhead
- Cache can be force-refreshed by individual service health checks

### Exponential Backoff
- Automatic retry with exponential backoff (1s, 2s, 4s delays)
- Configurable retry parameters
- Comprehensive error logging

### Error Handling
- Specific exception handling for different failure types
- Detailed error messages in health check responses
- Graceful degradation when services are unavailable

### Monitoring
- Real-time health status for all external dependencies
- Timestamp tracking for last validation attempts
- Service availability statistics

## Best Practices

1. **Always use decorators** for external API calls to ensure reliability
2. **Monitor health endpoints** regularly in production
3. **Set appropriate timeout values** for API calls (recommended: 10 seconds)
4. **Handle fallback scenarios** when external services are unavailable
5. **Log API failures** for debugging and monitoring

## Example Implementation

Here's a complete example showing how to enhance an existing API function:

```python
# Before - unreliable API call
# def get_census_data(county_fips):
#     api_key = os.environ.get('CENSUS_API_KEY')
#     url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME&for=county:{county_fips}&key={api_key}"
#     response = requests.get(url)
#     return response.json()

# After - enhanced with local data files for strategic planning
from utils.census_data_loader import WisconsinCensusDataLoader

def get_census_data(county_name):
    """Get census data from local CSV files - no API required"""
    wisconsin_census = WisconsinCensusDataLoader()
    return {
        'mobile_home_percentage': wisconsin_census.get_mobile_home_percentage(county_name),
        'pct_aged_65_plus': wisconsin_census.get_elderly_population_percentage(county_name),
        'total_population': wisconsin_census.get_county_population(county_name)
    }
```

This enhancement provides automatic retries, API key validation, and proper error handling with minimal code changes.