# Contributing to WakeDock

Thank you for your interest in contributing to WakeDock! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Security](#security)

## 🤝 Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

### Our Standards

- **Be respectful** and inclusive of all contributors
- **Be patient** with new contributors and help them learn
- **Be constructive** when providing feedback
- **Focus on the issue**, not the person
- **Use welcoming and inclusive language**

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Git** (v2.25+)
- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Python** (v3.11+)
- **Node.js** (v18+)
- **npm** or **yarn**

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/wakedock.git
cd wakedock
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/original-owner/wakedock.git
```

## 💻 Development Setup

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your configuration
nano .env
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements-dev.txt

# Install Node.js dependencies for dashboard
cd dashboard
npm install
cd ..
```

### 3. Start Development Environment

```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up -d

# Or use the development script
./dev.sh
```

### 4. Verify Installation

```bash
# Check if all services are running
docker-compose ps

# Run health check
./scripts/health-check.sh

# Access the application
# - API: http://localhost:8000
# - Dashboard: http://localhost:3000
# - Caddy Admin: http://localhost:2019
```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Tests**
- 🎨 **UI/UX improvements**
- 🔧 **Performance optimizations**
- 🌐 **Translations**

### Before You Start

1. **Check existing issues** to see if your idea is already being worked on
2. **Create an issue** to discuss new features or significant changes
3. **Review the roadmap** to understand project direction
4. **Check the TODO list** for priority items

## 🔄 Pull Request Process

### 1. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Follow the [coding standards](#coding-standards)
- Write or update tests as needed
- Update documentation if required
- Keep commits atomic and well-described

### 3. Test Your Changes

```bash
# Run the test suite
pytest

# Run frontend tests
cd dashboard
npm test
cd ..

# Run linting
black src/
isort src/
flake8 src/

# Run health checks
./scripts/health-check.sh --detailed
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add service auto-discovery feature

- Implement Docker API integration for service detection
- Add configuration options for discovery intervals
- Include tests for new functionality
- Update documentation with usage examples

Closes #123"
```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

### 5. Push and Create PR

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
# Use the provided PR template
```

### PR Requirements

- ✅ **Descriptive title** and detailed description
- ✅ **Reference related issues** using `Closes #123`
- ✅ **All tests pass** (CI will verify)
- ✅ **Code coverage** maintained or improved
- ✅ **Documentation updated** if needed
- ✅ **No merge conflicts** with main branch

## 📏 Coding Standards

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some customizations:

```python
# Use Black for formatting
black src/ tests/

# Use isort for import sorting
isort src/ tests/

# Use flake8 for linting
flake8 src/ tests/
```

**Key Guidelines:**
- Maximum line length: 88 characters (Black default)
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Use descriptive variable and function names
- Follow the principle of least surprise

### JavaScript/TypeScript Style

For frontend code:

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

**Key Guidelines:**
- Use TypeScript for all new code
- Follow ESLint configuration
- Use Prettier for formatting
- Prefer functional components and hooks
- Use semantic variable names

### File Organization

```
src/wakedock/
├── api/                 # API endpoints and routes
├── core/               # Core business logic
├── database/           # Database models and migrations
├── security/           # Authentication and security
├── utils/              # Utility functions
└── __init__.py

tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
└── e2e/               # End-to-end tests
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/wakedock

# Run specific test file
pytest tests/unit/test_orchestrator.py

# Run tests with specific marker
pytest -m "slow"
```

### Writing Tests

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete user workflows

Example test structure:

```python
import pytest
from unittest.mock import Mock, patch

from wakedock.core.orchestrator import DockerOrchestrator


class TestDockerOrchestrator:
    """Test suite for DockerOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return DockerOrchestrator()
    
    def test_service_creation(self, orchestrator):
        """Test service creation functionality."""
        # Arrange
        service_config = {...}
        
        # Act
        result = orchestrator.create_service(service_config)
        
        # Assert
        assert result.success is True
        assert result.service_id is not None
```

### Test Coverage

- Maintain **minimum 80%** code coverage
- Focus on **critical paths** and **edge cases**
- Mock external dependencies
- Use **fixtures** for common test data

## 📚 Documentation

### Types of Documentation

1. **Code Documentation**
   - Docstrings for all public APIs
   - Inline comments for complex logic
   - Type hints for better IDE support

2. **User Documentation**
   - API documentation (generated from code)
   - Configuration guides
   - Deployment instructions
   - Troubleshooting guides

3. **Developer Documentation**
   - Architecture decisions
   - Development setup
   - Contributing guidelines

### Writing Documentation

- Use **clear, concise language**
- Include **practical examples**
- Keep documentation **up-to-date** with code changes
- Use **proper markdown formatting**

Example docstring format:

```python
def create_service(self, config: ServiceConfig) -> ServiceResult:
    """Create a new Docker service.
    
    Args:
        config: Service configuration including image, ports, and environment.
        
    Returns:
        ServiceResult containing success status and service details.
        
    Raises:
        ServiceCreationError: If service creation fails.
        ValidationError: If configuration is invalid.
        
    Example:
        >>> config = ServiceConfig(image="nginx:latest", ports=["80:80"])
        >>> result = orchestrator.create_service(config)
        >>> print(result.service_id)
        'service_123'
    """
```

## 🐛 Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check the FAQ** and documentation
3. **Try the latest version** to see if it's already fixed
4. **Gather relevant information** (logs, configuration, etc.)

### Creating a Good Issue

Use our issue templates and include:

- **Clear title** describing the problem
- **Step-by-step reproduction** instructions
- **Expected vs actual behavior**
- **Environment details** (OS, Docker version, etc.)
- **Relevant logs** and error messages
- **Screenshots** if applicable

### Issue Labels

We use labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority/high`: High priority issue
- `status/in-progress`: Currently being worked on

## 🔒 Security

### Reporting Security Vulnerabilities

**Do not report security vulnerabilities in public issues.**

Instead:

1. Email us at `security@wakedock.dev`
2. Include detailed information about the vulnerability
3. Provide steps to reproduce if possible
4. Allow time for us to address the issue before public disclosure

### Security Best Practices

When contributing:

- **Never commit secrets** (passwords, API keys, etc.)
- **Use environment variables** for configuration
- **Validate all inputs** and sanitize outputs
- **Follow secure coding practices**
- **Keep dependencies updated**

## 📞 Getting Help

### Community Support

- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: Join our community chat
- **Stack Overflow**: Tag questions with `wakedock`

### Maintainer Contact

- **GitHub Issues**: For bugs and feature requests
- **Email**: For security issues and private matters
- **Discord**: For real-time discussion

## 🏆 Recognition

Contributors are recognized in:

- **README.md** contributors section
- **CHANGELOG.md** release notes
- **GitHub** contributor graphs
- **Discord** special roles for active contributors

## 📄 License

By contributing to WakeDock, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE) file).

---

Thank you for contributing to WakeDock! Your efforts help make this project better for everyone. 🙏
