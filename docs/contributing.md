# Contributing to CARA

Welcome to the CARA (Comprehensive Automated Risk Assessment) project! We appreciate your interest in contributing to this open-source public health risk assessment platform developed at Georgetown University for Wisconsin public health departments.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Contribution Workflow](#contribution-workflow)
- [Documentation](#documentation)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Project Overview

CARA is a geospatial health and emergency preparedness risk assessment platform that:
- Serves 95 Wisconsin public health jurisdictions (including 11 tribal nations)
- Provides multi-domain risk scoring for natural hazards, infectious disease, and emergency preparedness
- Integrates real-time data from multiple government APIs
- Focuses on strategic long-term planning rather than emergency response

### Prerequisites

Before contributing, ensure you have:
- Python 3.11 or higher
- Git version control
- Basic understanding of Flask web development
- Familiarity with geospatial data (helpful but not required)
- Understanding of public health concepts (helpful but not required)

## Development Environment

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/cara-platform.git
   cd cara-platform
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database:**
   ```bash
   python -c "from core import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run the application:**
   ```bash
   python main.py
   ```

### Testing Your Setup

```bash
# Run the test suite
pytest tests/

# Run with coverage
make test

# Check code style
flake8 .

# Type checking (if you add type hints)
mypy .
```

## Code Standards

### Python Code Style

We follow **PEP 8** with these specific guidelines:

```python
# Good: Descriptive function names with docstrings
def calculate_risk_score(county_name: str, risk_type: str) -> Dict[str, float]:
    """
    Calculate risk score for a specific county and risk type.
    
    Args:
        county_name (str): Name of Wisconsin county
        risk_type (str): Type of risk assessment
        
    Returns:
        Dict[str, float]: Risk assessment results
    """
    pass

# Good: Clear variable names
jurisdiction_count = len(wisconsin_jurisdictions)
heat_vulnerability_score = 0.75

# Avoid: Unclear abbreviations
jc = len(wj)  # Bad
hvs = 0.75    # Bad
```

### Documentation Requirements

**All functions and classes must include docstrings:**

```python
def process_census_data(api_key: str, fips_code: str) -> Dict:
    """
    Process census data for a specific geographic area.
    
    This function retrieves and processes demographic data from the US Census
    Bureau API for risk assessment calculations.
    
    Args:
        api_key (str): Valid Census Bureau API key
        fips_code (str): Federal Information Processing Standards code
        
    Returns:
        Dict: Processed census data including population, demographics,
              and housing characteristics
              
    Raises:
        ValueError: If FIPS code is invalid
        ConnectionError: If Census API is unavailable
        
    Example:
        >>> data = process_census_data("your_key", "55025")
        >>> print(data['population'])
        590875
    """
```

### File Organization

```
cara-platform/
├── core.py                 # Application factory
├── app.py                  # Main routes and blueprints  
├── models.py               # Database models
├── utils/                  # Utility modules
│   ├── risk_calculation.py # Risk assessment logic
│   ├── data_processor.py   # Data processing utilities
│   └── api_helpers.py      # API interaction helpers
├── tests/                  # Test suite
├── docs/                   # Documentation
├── static/                 # CSS, JavaScript, images
└── templates/              # Jinja2 templates
```

### Git Commit Guidelines

Use conventional commit format:

```bash
# Format: <type>(<scope>): <description>

# Examples:
feat(risk): add climate-adjusted heat risk calculation
fix(api): handle timeout errors in census data retrieval
docs(readme): update installation instructions
test(utils): add tests for geo data processing
refactor(core): improve database connection handling
```

## Testing Guidelines

### Writing Tests

Create tests for all new functionality:

```python
# tests/test_risk_calculation.py
import pytest
from utils.risk_calculation import calculate_heat_risk

def test_heat_risk_calculation():
    """Test heat risk calculation for known county."""
    result = calculate_heat_risk("Dane", "high_heat_day")
    
    assert result['overall_risk'] > 0
    assert result['overall_risk'] <= 1.0
    assert 'exposure' in result
    assert 'vulnerability' in result
    assert 'resilience' in result

def test_heat_risk_invalid_county():
    """Test error handling for invalid county name."""
    with pytest.raises(ValueError):
        calculate_heat_risk("NonexistentCounty", "high_heat_day")
```

### Test Categories

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test external API integrations
4. **End-to-End Tests**: Test complete workflows

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_risk_calculation.py

# Run with coverage
pytest --cov=utils --cov-report=html

# Run tests for specific functionality
pytest -k "heat_risk"
```

## Contribution Workflow

### 1. Issue Creation

Before starting work:
- Check existing issues for duplicates
- Create detailed issue describing the problem or feature
- Wait for maintainer feedback before starting large changes

### 2. Branch Management

```bash
# Create feature branch
git checkout -b feature/climate-risk-enhancement

# Create fix branch  
git checkout -b fix/api-timeout-handling

# Create documentation branch
git checkout -b docs/deployment-guide-update
```

### 3. Making Changes

- Make focused, atomic commits
- Test thoroughly before submitting
- Update documentation as needed
- Follow code style guidelines

### 4. Pull Request Process

1. **Create Pull Request** with descriptive title and description
2. **Include testing information** and any breaking changes
3. **Request review** from maintainers
4. **Address feedback** promptly and thoroughly
5. **Ensure CI passes** before requesting final review

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Wisconsin Public Health Impact
Describe how this change affects Wisconsin public health departments.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings for all functions/classes
2. **API Documentation**: Document all public interfaces
3. **User Guides**: Help for Wisconsin public health departments
4. **Developer Guides**: Technical implementation details

### Documentation Standards

- Use clear, accessible language
- Include practical examples
- Explain Wisconsin-specific context
- Update documentation with code changes

## Community Guidelines

### Inclusive Environment

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Technical background
- Geographic location
- Professional role in public health

### Communication

- **Be respectful** in all interactions
- **Ask questions** when unclear about requirements
- **Provide context** for Wisconsin public health needs
- **Share knowledge** about public health workflows

### Public Health Focus

Remember that CARA serves real public health departments:
- **Prioritize accuracy** over speed in risk calculations
- **Consider real-world usability** for busy health officials
- **Respect privacy** and data sensitivity requirements
- **Test thoroughly** as decisions impact public safety

### Getting Help

- **Technical Questions**: Create GitHub issues
- **Public Health Context**: Consult with Georgetown research team
- **Wisconsin-Specific Questions**: Reference Wisconsin DHS resources

## Specialized Contribution Areas

### Risk Assessment Algorithms

If contributing to risk calculations:
- Provide scientific references for methodologies
- Include confidence intervals and uncertainty measures
- Document data sources and assumptions
- Consider equity implications of algorithms

### Geospatial Features

For mapping and geographic functionality:
- Test with Wisconsin county boundaries
- Consider tribal jurisdiction boundaries
- Validate coordinate reference systems
- Ensure accessibility of map features

### API Integrations

When working with external APIs:
- Include comprehensive error handling
- Document rate limits and quotas
- Provide fallback data when APIs are unavailable
- Test with real API keys and responses

### Data Processing

For data handling improvements:
- Document data sources and update frequencies
- Include data validation and quality checks
- Consider scalability for statewide deployment
- Maintain data provenance and lineage

---

Thank you for contributing to CARA! Your work helps protect Wisconsin communities by providing public health departments with the tools they need for effective emergency preparedness and response planning.

## Support

For additional support:
- **Email**: [research-team@georgetown.edu]
- **Issues**: GitHub issue tracker
- **Documentation**: `docs/` directory

*This contributing guide is maintained as part of the CARA platform documentation. Last updated: January 2024*