# Development Guide

## Setup Development Environment

### 1. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Install Git Hooks

We use `pre-commit` to enforce code quality standards automatically.

```bash
# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type pre-push
```

## Code Quality Checks

### Pre-commit Hooks (Runs on `git commit`)

The following checks run automatically before each commit:
- **black**: Code formatting (auto-fixes)
- **isort**: Import sorting (auto-fixes)
- **flake8**: Linting
- **trailing-whitespace**: Remove trailing whitespace (auto-fixes)
- **end-of-file-fixer**: Ensure files end with newline (auto-fixes)
- **check-yaml**: YAML syntax validation
- **check-added-large-files**: Prevent large files
- **check-merge-conflicts**: Detect merge conflicts

### Pre-push Hooks (Runs on `git push`)

- **mypy**: Static type checking

### Manual Checks

You can run all checks manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run black --all-files
pre-commit run mypy --all-files
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov=cli --cov=app

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Test Coverage Requirements

- Minimum coverage: 70%
- Target coverage: 75%+

## Code Style Guidelines

### Formatting

- Line length: 120 characters
- Use black for formatting
- Use isort for import sorting

### Type Hints

- All functions should have type hints
- Use `mypy` for type checking
- Avoid `Any` when possible

### Imports

- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports from `src/`

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline runs on:
- Push to `master` or `develop`
- Pull requests to `master` or `develop`
- Tags starting with `v*`

### Pipeline Stages

1. **Test and Code Quality** (Python 3.11 & 3.12)
   - Install dependencies
   - Lint with flake8
   - Check formatting with black
   - Check imports with isort
   - Type check with mypy
   - Run tests with pytest
   - Upload coverage reports

2. **Build and Push Add-on Images** (only on master/tags)
   - Build multi-arch Docker images
   - Push to GitHub Container Registry
   - Update addon version

## Troubleshooting

### Pre-commit Hook Failures

If a pre-commit hook fails:

1. Check the error message
2. Fix the issues manually or let auto-fixers do it
3. Stage the changes: `git add .`
4. Try committing again

### Skip Hooks (Not Recommended)

```bash
# Skip pre-commit hooks (use only when necessary)
git commit --no-verify

# Skip pre-push hooks
git push --no-verify
```

### Update Hooks

```bash
# Update pre-commit hooks to latest versions
pre-commit autoupdate
```
