# CI/CD Setup Guide

This document explains how to set up and configure the project's CI/CD process, including GitHub Actions and SonarQube integration.

## Table of Contents

1. [GitHub Actions Setup](#github-actions-setup)
2. [SonarQube Integration](#sonarqube-integration)
3. [Code Quality Tools](#code-quality-tools)
4. [Local Development Environment](#local-development-environment)

---

## GitHub Actions Setup

### 1. CI/CD Pipeline Overview

The project uses GitHub Actions for continuous integration and deployment. The following checks are automatically executed on every push or pull request:

- **Code Quality Checks**: flake8, black, isort, mypy
- **Unit Tests**: pytest for all modules
- **Test Coverage**: Generate and upload coverage reports
- **Security Scanning**: bandit, safety, pip-audit
- **SonarQube Analysis**: Code quality and technical debt analysis
- **Docker Build Test**: Ensure Docker image builds correctly

### 2. Required GitHub Secrets

The following secrets need to be configured in GitHub repository settings:

#### Codecov (Optional)
```
CODECOV_TOKEN=<your-codecov-token>
```
How to obtain:
1. Visit https://codecov.io
2. Sign in with GitHub account
3. Add project and get token

#### SonarQube (Required, if using SonarQube)
```
SONAR_TOKEN=<your-sonar-token>
SONAR_HOST_URL=<your-sonarqube-server-url>
```

How to obtain:

**Option 1: Use SonarCloud (Recommended for open source projects)**
1. Visit https://sonarcloud.io
2. Sign in with GitHub account
3. Add organization and project
4. Generate token: Account > Security > Generate Tokens
5. Set secrets:
   - `SONAR_TOKEN`: Generated token
   - `SONAR_HOST_URL`: `https://sonarcloud.io`

**Option 2: Self-hosted SonarQube Server**
1. Deploy SonarQube Server (using Docker):
   ```bash
   docker run -d --name sonarqube \
     -p 9000:9000 \
     -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
     sonarqube:community
   ```
2. Visit http://localhost:9000 (default credentials: admin/admin)
3. Create new project and generate token
4. Set secrets:
   - `SONAR_TOKEN`: Generated token
   - `SONAR_HOST_URL`: Your SonarQube Server URL

### 3. Workflow File Structure

```
.github/
└── workflows/
    └── ci.yml    # Main CI/CD workflow
```

### 4. Trigger Conditions

- **Push events**: Pushes to `master` or `develop` branch
- **Pull Request events**: PRs targeting `master` or `develop` branch

### 5. Workflow Description

#### Job 1: test
- Execution environment: Ubuntu Latest
- Python versions: 3.11, 3.12 (matrix build)
- Steps:
  1. Checkout code
  2. Setup Python environment
  3. Cache dependencies
  4. Install dependencies
  5. Lint check (flake8)
  6. Format check (black)
  7. Import order check (isort)
  8. Type check (mypy)
  9. Run tests and generate coverage report
  10. Upload coverage to Codecov
  11. SonarQube scan
  12. Upload test results

#### Job 2: security
- Security scanning:
  - `bandit`: Python code security vulnerability scanning
  - `safety`: Check for known vulnerabilities in dependencies
  - `pip-audit`: PyPI package security audit

#### Job 3: docker
- Test Docker image build
- Verify application runs correctly in container

---

## SonarQube Integration

### 1. Project Configuration

SonarQube configuration file: `sonar-project.properties`

Main configuration items:
```properties
sonar.projectKey=trash_tracking
sonar.projectName=Trash Tracking System
sonar.projectVersion=1.0.0

sonar.sources=src,cli.py,app.py
sonar.tests=tests

sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=test-results.xml
```

### 2. Quality Gate Settings

Recommended Quality Gate standards:
- Coverage: >= 80%
- Code duplication: <= 3%
- Maintainability rating: A
- Reliability rating: A
- Security rating: A
- Technical debt ratio: <= 5%

### 3. View Analysis Results

1. After pushing code, GitHub Actions will automatically execute SonarQube scan
2. Visit your SonarQube Server/SonarCloud to view detailed reports
3. Quality Gate status will be displayed in GitHub PR

---

## Code Quality Tools

### 1. Flake8 (Linting)

Configuration file: `.flake8`

Run command:
```bash
flake8 src tests cli.py app.py
```

Main checks:
- PEP 8 style violations
- Syntax errors
- Unused variables
- Code complexity

### 2. Black (Formatting)

Configuration file: `pyproject.toml` -> `[tool.black]`

Run commands:
```bash
# Check
black --check src tests cli.py app.py

# Auto-format
black src tests cli.py app.py
```

### 3. isort (Import Ordering)

Configuration file: `pyproject.toml` -> `[tool.isort]`

Run commands:
```bash
# Check
isort --check-only src tests cli.py app.py

# Auto-sort
isort src tests cli.py app.py
```

### 4. mypy (Type Checking)

Configuration file: `pyproject.toml` -> `[tool.mypy]`

Run command:
```bash
mypy src --ignore-missing-imports
```

### 5. Run All Checks at Once

Create `Makefile` or use the following script:

```bash
#!/bin/bash
# check_code.sh

echo "Running flake8..."
flake8 src tests cli.py app.py

echo "Running black..."
black --check src tests cli.py app.py

echo "Running isort..."
isort --check-only src tests cli.py app.py

echo "Running mypy..."
mypy src --ignore-missing-imports

echo "Running tests..."
pytest tests/ --cov=src --cov-report=term-missing

echo "All checks passed!"
```

---

## Local Development Environment

### 1. Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### 2. Pre-commit Hooks (Recommended)

Install pre-commit:
```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Enable pre-commit:
```bash
pre-commit install
```

### 3. Local Testing Workflow

Pre-push checklist:

```bash
# 1. Run code formatting
black src tests cli.py app.py
isort src tests cli.py app.py

# 2. Run linting
flake8 src tests cli.py app.py

# 3. Run type checking
mypy src --ignore-missing-imports

# 4. Run tests
pytest tests/ --cov=src --cov-report=html

# 5. Check coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### 4. Test Coverage Goals

- **Overall target**: >= 80%
- **Critical modules**: >= 90%
  - `src/models/`
  - `src/core/state_manager.py`
  - `src/api/routes.py`

---

## Common Issues

### Q1: CI failure: flake8 error

**Solution**:
```bash
# Run locally and fix
flake8 src tests cli.py app.py

# Common issues:
# - E501: Line too long (use black to auto-format)
# - F401: Unused import (manually remove)
# - E402: Import not at top of file (move to file beginning)
```

### Q2: CI failure: black format check

**Solution**:
```bash
# Auto-format
black src tests cli.py app.py

# Commit changes
git add .
git commit -m "style: apply black formatting"
```

### Q3: CI failure: insufficient test coverage

**Solution**:
```bash
# Check which code lacks tests
pytest tests/ --cov=src --cov-report=term-missing

# Add tests for uncovered modules
# Goal: Achieve 80%+ coverage
```

### Q4: SonarQube Quality Gate failure

**Possible causes**:
- High code duplication
- Excessive technical debt
- Security vulnerabilities
- Insufficient coverage

**Solution**:
1. Log in to SonarQube to view detailed report
2. Fix issues according to recommendations
3. Re-commit

---

## Continuous Improvement

### Monitoring Metrics

Regularly check the following metrics:
- Test coverage trends
- Code complexity
- Technical debt
- Number of security vulnerabilities
- Build time

### Optimization Recommendations

1. **Reduce build time**:
   - Use caching (already enabled)
   - Run tests in parallel
   - Optimize Docker builds

2. **Improve code quality**:
   - Regular refactoring
   - Reduce code complexity
   - Increase test coverage

3. **Enhance security**:
   - Regularly update dependencies
   - Fix security vulnerabilities
   - Use latest base images

---

## Reference Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
