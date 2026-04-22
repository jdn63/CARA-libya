# CARA API Security Guide

## Overview
The CARA platform includes comprehensive security features to protect Wisconsin public health data and ensure authorized access to risk assessment APIs.

## Security Features

### API Key Authentication
All API endpoints under `/api/*` require valid API keys for access:

**Access Levels:**
- **Admin**: Full system access (scheduler, data refresh)
- **Write**: Data modification capabilities
- **Readonly**: View data only (recommended for most users)

**Authentication Methods:**
1. **Header**: `X-API-Key: your_api_key_here`
2. **Authorization**: `Authorization: Bearer your_api_key_here`
3. **Query Parameter**: `?api_key=your_api_key_here`

### Rate Limiting
- **General**: 1000 requests/hour, 100 requests/minute
- **API Endpoints**: 300 requests/hour, 60 requests/minute
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Security Headers
- **Content Security Policy**: Prevents XSS attacks
- **Strict Transport Security**: Forces HTTPS
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing

## Protected API Endpoints

### Readonly Access Required
- `GET /api/historical-data/<jurisdiction_id>`
- `GET /api/predictive-analysis/<jurisdiction_id>`
- `GET /api/herc-region/<region_id>`
- `GET /api/herc-regions`
- `GET /api/wem-region/<region_id>`
- `GET /api/wem-regions`
- `GET /api/herc-boundaries`
- `GET /api/wem-boundaries`

### Admin Access Required
- `GET /api/scheduler-status`
- `POST /api/refresh-data/<source>`

## Example Usage

### Successful API Call
```bash
curl -H "X-API-Key: cara_ro_1757433000_abc123..." \
https://cara.replit.app/api/herc-regions
```

### Failed Authentication
```bash
curl https://cara.replit.app/api/herc-regions
# Returns: {"error": "Authentication Failed", "message": "API key required", "status_code": 401}
```

## For Wisconsin Public Health Departments

### Requesting API Access
Contact the CARA development team with:
1. **Department Information**: Name, jurisdiction, contact person
2. **Use Case**: How you'll use the API
3. **Access Level**: Readonly (recommended) or higher access needs
4. **Technical Contact**: For key delivery and support

### Security Best Practices
1. **Store Keys Securely**: Never commit API keys to code repositories
2. **Environment Variables**: Use secure environment variable storage
3. **Rate Limiting**: Implement exponential backoff for failed requests
4. **Monitoring**: Monitor your API usage and key expiration

### Error Handling
```python
import requests

def safe_api_call(endpoint, api_key):
headers = {'X-API-Key': api_key}
try:
response = requests.get(endpoint, headers=headers)
if response.status_code == 401:
# Handle authentication error
print("API key invalid or expired")
elif response.status_code == 429:
# Handle rate limiting
print("Rate limit exceeded, wait before retrying")
elif response.status_code == 200:
return response.json()
except requests.RequestException as e:
print(f"Request failed: {e}")
return None
```

## Monitoring and Logging

All API access is logged including:
- Request timestamp and endpoint
- API key access level (without exposing key)
- Success/failure status
- Rate limiting events
- Security violations

## Emergency Contact

For urgent security issues or compromised API keys, contact:
- **CARA Support**: Via feedback form at `/docs/feedback`
- **Emergency**: Contact Wisconsin Department of Health Services Emergency Operations