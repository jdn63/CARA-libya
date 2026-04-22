# Contributing to CARA

Thank you for your interest in contributing to CARA (Comprehensive Automated Risk Assessment). We welcome contributions from the public health, emergency management, data science, and software development communities.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment. We are committed to providing a welcoming and inclusive experience for everyone.

## How to Contribute

### Reporting Bugs

1. Check the [existing issues](https://github.com/jdn63/CARA/issues) to see if the bug has already been reported.
2. If not, open a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the problem
   - Expected vs. actual behavior
   - Your environment (Python version, OS, browser)
   - Screenshots if applicable

### Suggesting Features

Open an issue with the `enhancement` label describing:
- The problem your feature would solve
- How public health practitioners would benefit
- Any relevant data sources or methodologies

### Submitting Code Changes

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Set up your development environment:**
   ```bash
   pip install -r requirements.txt
   ```
   You will need:
   - Python 3.11+
   - PostgreSQL with PostGIS extension
   - Environment variables: `DATABASE_URL`, `SESSION_SECRET`

3. **Make your changes** following the coding standards below.

4. **Run existing tests** to make sure nothing is broken:
   ```bash
   pytest tests/
   ```

5. **Commit your changes** with a clear message:
   ```bash
   git commit -m "Add: brief description of your change"
   ```

6. **Push and open a Pull Request** against `main`:
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines

- Provide a clear description of what changed and why
- Reference any related issues (e.g., `Fixes #42`)
- Keep PRs focused on a single concern
- Add or update tests for new functionality
- Update documentation if your change affects the methodology or user-facing behavior
- Ensure all existing tests pass before submitting

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style conventions
- Use meaningful, descriptive variable and function names
- Add docstrings to all functions, classes, and modules
- Use the project's logging framework (`logging.getLogger(__name__)`) instead of `print()` statements
- Use `except Exception:` rather than bare `except:` clauses
- Never expose raw exception details in user-facing error messages
- Never hardcode API keys, secrets, or credentials

### Templates (HTML/Jinja2)

- Follow Bootstrap 5 conventions for UI components
- Maintain accessibility standards (ARIA labels, semantic HTML)
- Use Jinja2 template inheritance with the existing `base.html`

### Data Integrity

This is critical for a public health risk assessment tool:

- **No fabricated data**: Never use `random` values or hardcoded fallback numbers where authentic data is expected. Return `0.0` with appropriate logging when data is unavailable. The historical trend endpoint uses deterministic hashlib-based variation for synthetic research data, which is an accepted exception documented in the code.
- **Label all modeled data**: If a risk score is estimated, derived, or model-based rather than sourced from an external authority, it must be transparently disclosed in the methodology page and inline documentation.
- **Cite data sources**: Document the origin, refresh cadence, and limitations of any new data source.

### Security

- Never log or expose PII (personally identifiable information)
- Use parameterized queries for all database operations (SQLAlchemy ORM handles this)
- Add Subresource Integrity (SRI) hashes when including CDN resources
- API keys must only be accepted via HTTP headers, not query strings

## Project Structure

```
cara/
├── core.py                  # Application factory
├── main.py                  # Entry point
├── models.py                # SQLAlchemy database models
├── routes/                  # Flask blueprints
│   ├── api.py               # REST API endpoints
│   ├── dashboard.py         # Risk dashboard views
│   ├── herc.py              # HERC region views
│   ├── gis_export.py        # GIS data export
│   └── public.py            # Public pages
├── utils/                   # Business logic and data processing
│   ├── data_processor.py    # Core risk calculations
│   ├── security_manager.py  # API key and security management
│   └── ...                  # Domain-specific modules
├── templates/               # Jinja2 templates
├── static/                  # CSS, JS, images
├── data/                    # Local data files (census, climate, SVI)
├── config/                  # YAML configuration files
└── tests/                   # Test suite
```

## Areas Where We Especially Welcome Help

- **Test coverage**: The test suite is minimal and expanding it would greatly improve reliability.
- **Accessibility**: Improving screen reader support, keyboard navigation, and WCAG compliance.
- **Data validation**: Adding validation checks for data source freshness and consistency.
- **Documentation**: Improving inline code documentation and user-facing guides.
- **New data integrations**: Adding connections to additional authoritative public health data sources.

## License

By contributing to CARA, you agree that your contributions will be licensed under the [GNU Affero General Public License v3.0](LICENSE). This ensures CARA remains free and open for public good while requiring that any modified versions used as a network service also share their source code.

## Questions?

If you have questions about contributing, feel free to open an issue or contact the maintainer at **jdn63@georgetown.edu**.
