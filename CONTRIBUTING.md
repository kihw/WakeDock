# Contributing to WakeDock

Thank you for your interest in contributing to WakeDock! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security](#security)
- [Community](#community)

## Code of Conduct

This project adheres to the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.8+** installed
- **Node.js 18+** for dashboard development
- **Docker** and **Docker Compose** for containerized development
- **Git** for version control
- A **GitHub account** for pull requests

### First-time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/wakedock.git
   cd wakedock
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/originalowner/wakedock.git
   ```
4. **Set up development environment**:
   ```bash
   make setup
   # or
   ./dev.sh setup
   ```

## Development Setup

### Quick Start

```bash
# Install dependencies
make install

# Start development environment
make dev

# Run tests
make test

# Check code quality
make lint
```

### Development Tools

WakeDock provides several tools for development:

- **Makefile**: Build automation and common tasks
- **dev.sh**: Enhanced development script with comprehensive commands
- **Docker Compose**: Containerized development environment
- **Pre-commit hooks**: Automated code quality checks

### Environment Configuration

1. Copy example configuration:
   ```bash
   cp config/config.example.yml config/config.yml
   cp .env.example .env
   ```

2. Customize settings as needed for development

3. Start services:
   ```bash
   make start
   ```

## Contributing Process

### 1. Choose an Issue

- Browse [open issues](https://github.com/originalowner/wakedock/issues)
- Look for issues labeled `good first issue` for beginners
- Comment on the issue to indicate you're working on it

### 2. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Write clean, documented code
- Follow coding standards (see below)
- Add/update tests as needed
- Update documentation if necessary

### 4. Test Your Changes

```bash
# Run all tests
make test

# Run specific test suites
make test-python
make test-javascript
make test-integration

# Check code quality
make lint
make security
```

### 5. Commit Changes

We use [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
# Stage changes
git add .

# Commit with conventional format
git commit -m "feat: add new wake-on-lan feature"

# Or use commitizen for guided commits
cz commit
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots/demos if applicable
- Test results and coverage

### 7. Review Process

- Maintainers will review your PR
- Address feedback promptly
- Keep your branch updated with main
- Once approved, your PR will be merged

## Coding Standards

### Python Code

- Follow **PEP 8** style guide
- Use **Black** for code formatting (88 character line length)
- Use **isort** for import sorting
- Use **type hints** for all functions and methods
- Write **docstrings** for all public functions and classes

Example:
```python
from typing import List, Optional

def wake_device(mac_address: str, ip_address: Optional[str] = None) -> bool:
    """Wake a device using Wake-on-LAN.
    
    Args:
        mac_address: MAC address of the target device
        ip_address: Optional IP address for directed wake
        
    Returns:
        True if wake packet was sent successfully
        
    Raises:
        ValueError: If MAC address format is invalid
    """
    # Implementation here
    pass
```

### JavaScript/TypeScript Code

- Use **Prettier** for formatting
- Use **ESLint** for linting
- Prefer **TypeScript** for new code
- Use **async/await** over Promises
- Write **JSDoc** comments for complex functions

Example:
```typescript
/**
 * Fetch service status from the API
 * @param serviceId - Unique identifier for the service
 * @returns Promise resolving to service status
 */
async function getServiceStatus(serviceId: string): Promise<ServiceStatus> {
    const response = await fetch(`/api/v1/services/${serviceId}/status`);
    return response.json();
}
```

### Documentation

- Use **Markdown** for documentation
- Keep README files up to date
- Document all API endpoints
- Include code examples
- Write clear commit messages

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
├── e2e/                 # End-to-end tests
├── fixtures/            # Test data and fixtures
└── conftest.py          # Pytest configuration
```

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Group related tests in classes
- Use fixtures for common test data

Example:
```python
import pytest
from wakedock.core.wake import WakeService

class TestWakeService:
    """Test suite for WakeService functionality."""
    
    @pytest.fixture
    def wake_service(self):
        """Create a WakeService instance for testing."""
        return WakeService()
    
    def test_wake_device_with_valid_mac(self, wake_service):
        """Test waking device with valid MAC address."""
        result = wake_service.wake_device("00:11:22:33:44:55")
        assert result is True
    
    def test_wake_device_with_invalid_mac(self, wake_service):
        """Test waking device with invalid MAC address raises error."""
        with pytest.raises(ValueError):
            wake_service.wake_device("invalid-mac")
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-python

# With coverage
make coverage

# Specific test file
pytest tests/unit/test_wake.py -v

# Specific test method
pytest tests/unit/test_wake.py::TestWakeService::test_wake_device_with_valid_mac -v
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Inline comments and docstrings
2. **API Documentation**: Automatically generated from code
3. **User Documentation**: Setup, usage, and troubleshooting guides
4. **Developer Documentation**: Architecture, contributing, and development guides

### Documentation Standards

- Write clear, concise explanations
- Include practical examples
- Keep documentation up to date with code changes
- Use proper Markdown formatting
- Include diagrams where helpful

### Generating Documentation

```bash
# Generate API documentation
make docs

# Serve documentation locally
make docs-serve
```

## Security

### Security Guidelines

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Follow security best practices
- Run security checks regularly

### Security Checks

```bash
# Run all security checks
make security

# Python security
make security-python

# JavaScript security
make security-javascript

# Docker security
make security-docker
```

### Reporting Security Issues

Please report security vulnerabilities privately by emailing security@wakedock.com. Do not create public issues for security vulnerabilities.

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Email**: For security issues and private matters

### Getting Help

- Check existing [issues](https://github.com/originalowner/wakedock/issues) and [discussions](https://github.com/originalowner/wakedock/discussions)
- Read the [documentation](https://wakedock.readthedocs.io)
- Ask questions in [GitHub Discussions](https://github.com/originalowner/wakedock/discussions)

### Recognition

Contributors will be recognized in:
- [CHANGELOG.md](CHANGELOG.md) for their contributions
- GitHub contributor graphs
- Special thanks in release notes for significant contributions

## Development Workflow

### Daily Development

```bash
# Start development environment
make dev

# Make changes...

# Check code quality
make lint format

# Run tests
make test

# Commit changes
git add .
git commit -m "feat: implement new feature"
```

### Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create pull request
6. Tag release after merge

### Continuous Integration

All pull requests must pass:
- Code quality checks (linting, formatting)
- Security scans
- Test suite with >80% coverage
- Documentation builds

## Advanced Topics

### Adding New Features

When adding major features:

1. Create a design document
2. Discuss with maintainers
3. Break into smaller, reviewable PRs
4. Include comprehensive tests
5. Update documentation

### Performance Considerations

- Profile code for performance bottlenecks
- Consider resource usage (memory, CPU)
- Test with realistic data volumes
- Document performance characteristics

### Backward Compatibility

- Maintain API compatibility when possible
- Follow semantic versioning
- Provide migration guides for breaking changes
- Deprecate features before removal

## Questions?

If you have questions not covered in this guide:

1. Check the [FAQ](docs/FAQ.md)
2. Search [existing issues](https://github.com/originalowner/wakedock/issues)
3. Ask in [GitHub Discussions](https://github.com/originalowner/wakedock/discussions)
4. Create a new issue with the `question` label

Thank you for contributing to WakeDock! 🐳
