# Publishing Guide for TokenBudget

## Pre-Publishing Checklist

### 1. Test Locally
```bash
cd /home/user/Desktop/tokenbudget

# Install in development mode
pip install -e ".[dev,all]"

# Run tests
pytest tests/ -v

# Type checking (optional)
mypy src/tokenbudget

# Linting (optional)
ruff check src/
```

### 2. Build the Package
```bash
# Install build tools
pip install build twine

# Build distribution
python -m build
```

This creates:
- `dist/tokenbudget-0.1.0.tar.gz` (source distribution)
- `dist/tokenbudget-0.1.0-py3-none-any.whl` (wheel)

### 3. Test on TestPyPI (Optional but Recommended)
```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ tokenbudget
```

### 4. Publish to PyPI
```bash
# Upload to PyPI
python -m twine upload dist/*

# Enter your PyPI credentials when prompted
```

### 5. Verify Installation
```bash
pip install tokenbudget
python -c "from tokenbudget import TokenTracker; print('Success!')"
```

## GitHub Repository Setup

### 1. Create Repository
```bash
cd /home/user/Desktop/tokenbudget
git init
git add .
git commit -m "Initial commit: TokenBudget v0.1.0"
```

### 2. Push to GitHub
```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/tokenbudget.git
git branch -M main
git push -u origin main
```

### 3. Create Release
- Go to GitHub > Releases > Create new release
- Tag: `v0.1.0`
- Title: `TokenBudget v0.1.0`
- Description: Copy from README features section

### 4. Enable GitHub Actions
The CI workflow (`.github/workflows/ci.yml`) will run automatically on:
- Push to `main` or `dev` branches
- Pull requests to `main`

## PyPI Account Setup

### 1. Create PyPI Account
- Go to https://pypi.org/account/register/
- Verify email

### 2. Generate API Token
- Go to Account Settings > API tokens
- Create token for "tokenbudget" project
- Save token securely

### 3. Configure Credentials
```bash
# Option 1: Use token directly
python -m twine upload dist/* -u __token__ -p pypi-YOUR_TOKEN_HERE

# Option 2: Create ~/.pypirc
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
EOF
chmod 600 ~/.pypirc
```

## Post-Publishing

### 1. Update README Badges
Once published, the PyPI badge will work automatically:
```markdown
[![PyPI version](https://badge.fury.io/py/tokenbudget.svg)](https://badge.fury.io/py/tokenbudget)
```

### 2. Announce
- Twitter/X
- Reddit (r/Python, r/MachineLearning)
- Hacker News
- Dev.to blog post

### 3. Monitor
- Watch PyPI download stats
- Respond to GitHub issues
- Update documentation as needed

## Version Updates

For future releases:

1. Update version in `pyproject.toml`
2. Update `__version__` in `src/tokenbudget/__init__.py`
3. Run tests
4. Build and upload:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
5. Tag release on GitHub

## Troubleshooting

### Build Errors
```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info
python -m build
```

### Import Errors
Check that `src/tokenbudget/__init__.py` exports all public APIs.

### Test Failures
```bash
# Run specific test
pytest tests/test_tracker.py -v

# Run with coverage
pytest tests/ --cov=tokenbudget --cov-report=html
```

## Success!

Your package is now live on PyPI and anyone can install it with:
```bash
pip install tokenbudget
```
