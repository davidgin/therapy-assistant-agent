# Testing Framework for Therapy Assistant Agent

This directory contains comprehensive unit and integration tests for the therapy-assistant-agent project.

## Overview

The testing framework provides comprehensive coverage for:
- **Authentication and authorization**
- **Voice analysis and audio processing**
- **Web interface functionality**
- **Database models and operations**
- **Utility functions and services**
- **API endpoint integration**

## Test Structure

```
tests/
├── conftest.py                          # Pytest configuration and fixtures
├── unit/                               # Unit tests
│   ├── __init__.py
│   ├── test_auth_endpoints.py         # Authentication endpoint tests
│   ├── test_audio_analysis.py         # Audio analysis service tests
│   ├── test_web_routes.py             # Web interface tests
│   ├── test_voice_endpoints.py        # Voice analysis endpoint tests
│   ├── test_database_models.py        # Database model tests
│   └── test_utility_functions.py      # Utility function tests
├── integration/                        # Integration tests
│   ├── __init__.py
│   └── test_api_integration.py        # API integration tests
└── README.md                          # This documentation
```

## Test Categories

### Unit Tests (`tests/unit/`)

#### Authentication Tests (`test_auth_endpoints.py`)
- **User registration and validation**
- **Login/logout functionality**
- **JWT token creation and verification**
- **Password hashing and verification**
- **Role-based access control**
- **API endpoint authentication**

#### Audio Analysis Tests (`test_audio_analysis.py`)
- **Speech recognition and transcription**
- **Audio feature extraction**
- **Tone and emotion classification**
- **Speech rate calculation**
- **Confidence scoring**
- **Error handling for audio processing**

#### Web Interface Tests (`test_web_routes.py`)
- **Login/logout web flows**
- **Dashboard access and rendering**
- **Diagnostic form submission**
- **Treatment recommendation forms**
- **Case study display**
- **Cookie-based authentication**

#### Voice Analysis Endpoint Tests (`test_voice_endpoints.py`)
- **Voice transcription endpoints**
- **Comprehensive voice analysis**
- **Rate limiting**
- **License validation for voice features**
- **Error handling and edge cases**

#### Database Model Tests (`test_database_models.py`)
- **User model CRUD operations**
- **Data validation and constraints**
- **Relationship queries**
- **Enum validations**
- **Timestamp handling**

#### Utility Function Tests (`test_utility_functions.py`)
- **Password utilities**
- **JWT utilities**
- **Settings configuration**
- **File I/O operations**
- **Security functions**
- **Validation utilities**

### Integration Tests (`tests/integration/`)

#### API Integration Tests (`test_api_integration.py`)
- **Complete authentication flows**
- **Voice analysis integration**
- **Web interface workflows**
- **Database integration**
- **Cross-service communication**

## Test Fixtures and Configuration

### Key Fixtures (`conftest.py`)

- **`async_db`** - Async database session for testing
- **`test_user`** - Standard test user with therapist role
- **`test_admin_user`** - Admin user for permission testing
- **`test_student_user`** - Student user for license validation
- **`auth_client`** - FastAPI test client for auth endpoints
- **`web_client`** - FastAPI test client for web interface
- **`mock_openai_client`** - Mocked OpenAI client
- **`mock_speech_recognizer`** - Mocked speech recognition
- **`sample_audio_data`** - Base64 encoded test audio data

### Test Markers

- **`@pytest.mark.unit`** - Unit tests
- **`@pytest.mark.integration`** - Integration tests
- **`@pytest.mark.auth`** - Authentication related
- **`@pytest.mark.voice`** - Voice analysis related
- **`@pytest.mark.web`** - Web interface related
- **`@pytest.mark.database`** - Database related
- **`@pytest.mark.slow`** - Slow running tests

## Running Tests

### Using pytest directly

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/ -m unit

# Run integration tests only
pytest tests/integration/ -m integration

# Run specific test categories
pytest -m auth          # Authentication tests
pytest -m voice         # Voice analysis tests
pytest -m web           # Web interface tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_endpoints.py

# Run with verbose output
pytest -v

# Run failed tests from last run
pytest --lf
```

### Using the test runner script

```bash
# Check test environment
python run_tests.py --check

# Run unit tests
python run_tests.py --unit

# Run integration tests
python run_tests.py --integration

# Run all tests with coverage
python run_tests.py --all

# Run specific marker
python run_tests.py --marker auth

# Run specific file
python run_tests.py --file tests/unit/test_auth_endpoints.py

# Generate coverage report
python run_tests.py --coverage

# Clean test artifacts
python run_tests.py --clean
```

## Test Coverage

The test suite aims for **80%+ code coverage** across:

### High Priority Coverage Areas
- **Authentication and security functions** (95%+)
- **Voice analysis core functionality** (90%+)
- **Database models and operations** (90%+)
- **API endpoint logic** (85%+)

### Medium Priority Coverage Areas
- **Web interface handlers** (80%+)
- **Utility functions** (80%+)
- **Configuration management** (75%+)

## Test Data and Mocking

### Mocked External Services
- **OpenAI API calls** - Mocked with realistic responses
- **Speech recognition** - Mocked transcription results
- **File I/O operations** - Temporary files and in-memory data
- **HTTP requests** - Mocked external API calls

### Test Data
- **Sample audio data** - Base64 encoded WAV files
- **Clinical case examples** - Realistic diagnostic scenarios
- **User data** - Various roles and license types
- **Voice analysis results** - Comprehensive analysis examples

## Best Practices

### Test Organization
- **One test class per major component**
- **Descriptive test method names**
- **Arrange-Act-Assert pattern**
- **Isolated test methods**

### Async Testing
- **Use `@pytest.mark.asyncio` for async tests**
- **Proper async/await patterns**
- **Async database session handling**
- **Async service mocking**

### Security Testing
- **Input validation testing**
- **SQL injection prevention**
- **XSS prevention**
- **Authentication bypass attempts**
- **Authorization validation**

### Performance Considerations
- **Fast test execution**
- **Efficient database operations**
- **Minimal external dependencies**
- **Parallel test execution support**

## Continuous Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python run_tests.py --all --verbose
    python run_tests.py --coverage
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
- Ensure test database is properly configured
- Check async session management
- Verify SQLAlchemy setup

#### Import Errors
- Check PYTHONPATH configuration
- Verify all dependencies are installed
- Check module import paths

#### Async Test Issues
- Use proper async fixtures
- Check event loop configuration
- Verify asyncio mode setting

#### Mock Configuration
- Ensure mocks are properly patched
- Check mock return values
- Verify async mock usage

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Run with debug logging
pytest --log-cli-level=DEBUG

# Run single test with debugging
pytest tests/unit/test_auth_endpoints.py::TestAuthenticationEndpoints::test_login_success -v -s
```

## Contributing

When adding new tests:

1. **Follow the existing patterns** in test organization
2. **Add appropriate markers** for test categorization
3. **Update fixtures** if new test data is needed
4. **Document complex test scenarios**
5. **Ensure proper cleanup** in teardown methods
6. **Add integration tests** for new features

## Test Metrics

Current test metrics:
- **Total Tests**: 100+ test methods
- **Coverage Target**: 80%+
- **Test Categories**: 8 markers
- **Fixture Count**: 20+ fixtures
- **Async Tests**: 60%+ of tests

## Security Considerations

The test suite includes specific security testing for:
- **Input sanitization**
- **Authentication bypass prevention**
- **Authorization validation**
- **SQL injection prevention**
- **XSS prevention**
- **Rate limiting validation**

These security tests help ensure the application is resilient against common attack vectors.