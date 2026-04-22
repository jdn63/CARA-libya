# Adding a Custom Data Connector

CARA's connector system makes it straightforward to add any data source —
national, regional, or local — without modifying the core risk engine.

## What a connector does

A connector is responsible for fetching data from one source for one jurisdiction
and returning a standardized Python dict. The risk engine calls connectors
through the ConnectorRegistry and passes their results to domain modules.

## Step 1: Create the connector file

Create a new file in `utils/connectors/global/` or `utils/connectors/us/`:

```python
# utils/connectors/global/my_data_source.py

import requests
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

class MyDataSourceConnector(BaseConnector):

    CACHE_DURATION_SECONDS = 86400

    def __init__(self, country_code: str, config: Optional[Dict] = None):
        super().__init__(config)
        self.country_code = country_code

    def is_available(self) -> bool:
        # Return True if the data source is reachable and credentials are set
        return True

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'My Data Source Name',
            'url': 'https://www.example.org',
            'update_frequency': 'Annual',
            'license': 'Public Domain',
            'geographic_coverage': 'Global',
            'notes': 'Any important caveats here.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        try:
            response = requests.get(
                'https://api.example.org/data',
                params={'country': self.country_code},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            return self._wrap({
                'my_metric': data.get('value'),
                'my_other_metric': data.get('other'),
                '_last_updated': '2026-01-01',
            })
        except Exception as e:
            return self._unavailable_response(f"My data source failed: {e}")
```

## Step 2: Register the connector

Open `utils/connector_registry.py` and add a new `elif` branch in `_build_connector()`:

```python
elif name == 'my_data_source':
    from utils.connectors.global.my_data_source import MyDataSourceConnector
    return MyDataSourceConnector(country_code=country_code)
```

## Step 3: Reference it in the profile

Open `config/profiles/international.yaml` (or `us_state.yaml`) and add
your connector under `connectors:`:

```yaml
connectors:
  my_domain: my_data_source
```

## Step 4: Use the data in a domain

In your domain's `calculate()` method, read from `connector_data`:

```python
def calculate(self, connector_data, jurisdiction_config, profile):
    my_data = connector_data.get('my_data_source', {})
    if my_data.get('available'):
        value = my_data.get('my_metric', 0)
        # ... incorporate into score
```

## Rules for connectors

1. Never raise exceptions from `fetch()`. Catch all errors and return
   `self._unavailable_response("explanation")` instead.

2. Always include `'available': True/False` in the return dict.
   Use `self._wrap(data)` for success and `self._unavailable_response(msg)` for failure.

3. Cache aggressively. Set `CACHE_DURATION_SECONDS` appropriately for your
   data source's update frequency. Daily is appropriate for most public health data.

4. Log at `debug` level inside connectors. The scheduler and registry will log
   higher-level outcomes.

5. Document the data source fully in `source_info()`. This appears in the
   methodology page seen by end users.

## Using the database cache

For connectors whose data changes infrequently, store results in the
`ConnectorDataCache` model to survive application restarts:

```python
from models import ConnectorDataCache
from app import db
from datetime import datetime

cache_record = ConnectorDataCache.query.filter_by(
    jurisdiction_id=jurisdiction_id,
    connector_name='my_data_source'
).first()

if cache_record and (datetime.utcnow() - cache_record.fetched_at).seconds < self.CACHE_DURATION_SECONDS:
    return cache_record.data

# ... fetch fresh data ...
result = self._wrap({...})

if not cache_record:
    cache_record = ConnectorDataCache(
        jurisdiction_id=jurisdiction_id,
        connector_name='my_data_source'
    )
cache_record.data = result
cache_record.fetched_at = datetime.utcnow()
cache_record.available = result.get('available', False)
db.session.merge(cache_record)
db.session.commit()
```
