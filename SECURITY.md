# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in CARA, **please do not open a public issue.** Instead, report it privately so we can address it before it is publicly disclosed.

### How to Report

Email the maintainer directly at **jdn63@georgetown.edu** with the subject line **"CARA Security Vulnerability"**.

Please include:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. The potential impact (e.g., data exposure, unauthorized access)
4. Any suggested fixes, if you have them

### What to Expect

- **Acknowledgment** within 72 hours of your report
- **Status update** within 7 days with an assessment and remediation timeline
- **Credit** in the release notes when the fix is published (unless you prefer to remain anonymous)

## Scope

The following are in scope for security reports:

- Authentication and authorization bypasses
- Injection vulnerabilities (SQL, XSS, template injection)
- Exposure of sensitive data (API keys, PII, internal system details)
- Insecure default configurations
- Dependency vulnerabilities with a known exploit path

The following are out of scope:

- Denial of service attacks
- Issues in third-party dependencies without a demonstrated exploit in CARA
- Social engineering
- Issues requiring physical access to the server

## Security Practices

CARA follows these security practices:

- **No PII storage**: The feedback system does not collect IP addresses or user-agent strings.
- **Error message sanitization**: Internal error details are logged server-side only; users see generic error messages.
- **API key security**: API keys are accepted only via HTTP headers (`X-API-Key` or `Authorization: Bearer`), never in URL query strings.
- **Subresource Integrity**: CDN-loaded CSS and JS resources include SRI hashes to prevent supply chain attacks.
- **Parameterized queries**: All database operations use SQLAlchemy ORM to prevent SQL injection.
- **Content Security Policy**: HTTP security headers are configured to mitigate XSS and clickjacking.
- **Rate limiting**: API endpoints are rate-limited to prevent abuse.
- **No secrets in code**: All sensitive configuration is loaded from environment variables.

## Supported Versions

Security fixes are applied to the latest release only. We recommend always running the most recent version of CARA.

| Version | Supported |
|---------|-----------|
| 2.4.x   | Yes       |
| < 2.4   | No        |
