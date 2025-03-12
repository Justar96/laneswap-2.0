# Contributing to LaneSwap

Thank you for your interest in contributing to LaneSwap! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes

```bash
# Clone your fork
git clone https://github.com/your-username/laneswap.git
cd laneswap

# Install development dependencies
pip install -e ".[dev]"
```

## Development Environment

LaneSwap uses the following tools for development:

- **pytest** for testing
- **black** for code formatting
- **isort** for import sorting
- **mypy** for type checking

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (skip integration tests)
pytest -m "not integration"

# Run with coverage report
pytest --cov=laneswap
```

## Code Style

We follow PEP 8 guidelines with some modifications:

- Line length is 88 characters (enforced by Black)
- Use double quotes for strings
- Use type annotations for function parameters and return values

Before submitting a pull request, please ensure your code passes all style checks:

```bash
# Format code with Black
black laneswap tests

# Sort imports with isort
isort laneswap tests

# Run type checking with mypy
mypy laneswap
```

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the tests to cover your changes
3. Ensure all tests pass and the code follows our style guidelines
4. Submit a pull request with a clear description of the changes

## Integration Tests

Some tests require external services like MongoDB or Discord webhooks. These are marked with the `integration` marker and are skipped by default in CI.

To run integration tests locally:

```bash
# Set environment variables for integration tests
export MONGODB_URI="mongodb://localhost:27017"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Run integration tests
pytest -m "integration"
```

## Release Process

1. Update version number in `__init__.py`, `setup.py`, and `pyproject.toml`
2. Update CHANGELOG.md with the changes
3. Create a new GitHub release with a tag matching the version number
4. The GitHub Actions workflow will automatically publish to PyPI

## Questions?

If you have any questions or need help, please open an issue on GitHub. 