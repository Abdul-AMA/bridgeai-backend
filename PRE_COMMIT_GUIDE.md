# Pre-Commit Validation Guide

## Overview

Before committing and pushing your code, run the pre-commit validation script to ensure your changes meet CI/CD requirements. This prevents failed builds and saves time.

## Quick Start

### Basic Check (Recommended)
```bash
python pre_commit_check.py
```

### Quick Check (Skip Tests & Security)
```bash
python pre_commit_check.py --quick
```

### Auto-Fix Issues
```bash
python pre_commit_check.py --fix
```

### Skip Tests Only
```bash
python pre_commit_check.py --skip-tests
```

## What Does It Check?

### 1. **Code Formatting** ✅
- **Black**: Python code formatting
- **isort**: Import statement sorting

### 2. **Code Linting** ✅
- **Flake8**: Code quality and PEP 8 compliance
- **MyPy**: Type checking (informational)

### 3. **Security Scans** 🔒
- **Bandit**: Security vulnerability detection
- **Safety**: Dependency vulnerability check

### 4. **Test Suite** 🧪
- **Pytest**: All unit and integration tests

## Workflow

### Before Every Commit

1. **Make your changes** to the code

2. **Run the pre-commit check:**
   ```bash
   python pre_commit_check.py --fix
   ```
   This will auto-fix formatting issues.

3. **If any checks fail:**
   - Review the error messages
   - Fix the reported issues
   - Re-run the script

4. **When all checks pass:**
   ```
   ✓ ALL CHECKS PASSED! You're ready to commit and push.
   ```

5. **Commit and push your code:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin your-branch
   ```

## Command Options

| Option | Description | Use Case |
|--------|-------------|----------|
| _(no flags)_ | Full validation | Before important commits |
| `--fix` | Auto-fix formatting | First run before commit |
| `--quick` | Skip tests & security | During active development |
| `--skip-tests` | Skip only tests | When tests take too long |

## Common Scenarios

### Scenario 1: Quick Development Iteration
```bash
# Make changes
python pre_commit_check.py --quick --fix
git add .
git commit -m "feat: add new feature"
```

### Scenario 2: Before PR/Merge
```bash
# Full validation
python pre_commit_check.py --fix
# Review output
git add .
git commit -m "fix: address review comments"
git push origin feature-branch
```

### Scenario 3: Tests Are Slow
```bash
# Skip tests locally, let CI run them
python pre_commit_check.py --skip-tests --fix
git add .
git commit -m "refactor: improve code structure"
```

## Troubleshooting

### "Module not found" Errors

Install the required tools:
```bash
pip install black isort flake8 mypy bandit safety pytest pytest-cov
```

### Black/isort Formatting Failures

Auto-fix:
```bash
python pre_commit_check.py --fix
```

Or manually:
```bash
python -m black app/ tests/
python -m isort app/ tests/
```

### Flake8 Linting Errors

Review the errors and fix manually. Common issues:
- Unused imports
- Line too long (>120 chars)
- Undefined variables
- Complex functions

### Bandit Security Warnings

Review the security issues:
```bash
python -m bandit -r app/ -ll
```

Most are false positives. Add `# nosec` comment if intentional.

### Tests Failing

Run tests individually to debug:
```bash
pytest tests/test_auth.py -v
pytest tests/test_projects.py -v
```

## Integration with Git Hooks (Optional)

### Install as Git Pre-Commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/sh
python pre_commit_check.py --quick
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

Now the checks run automatically before each commit!

## CI/CD Alignment

This script mirrors the GitHub Actions CI pipeline:

| Local Check | GitHub Actions Workflow | Job |
|-------------|------------------------|-----|
| Black | ci.yml | Code Quality & Linting |
| isort | ci.yml | Code Quality & Linting |
| Flake8 | ci.yml | Code Quality & Linting |
| MyPy | ci.yml | Code Quality & Linting |
| Bandit | security.yml | Code Security Analysis |
| Safety | security.yml | Dependency Security Scan |
| Pytest | ci.yml | Unit & Integration Tests |

## Performance Tips

**Fastest Check:**
```bash
python pre_commit_check.py --quick --fix
# ~10-20 seconds
```

**Standard Check (Skip Tests):**
```bash
python pre_commit_check.py --skip-tests --fix
# ~30-45 seconds
```

**Full Check:**
```bash
python pre_commit_check.py --fix
# ~2-5 minutes (depending on test suite)
```

## Best Practices

1. ✅ **Run `--quick --fix` frequently** during development
2. ✅ **Run full check** before creating/updating PRs
3. ✅ **Commit formatting fixes separately** from logic changes
4. ✅ **Fix issues immediately** rather than accumulating them
5. ✅ **Use `--fix` first** to auto-resolve formatting issues

## Success Example

```
==================================================================
        BridgeAI Backend - Pre-Commit Validation
==================================================================

==================================================================
                    1. Code Formatting
==================================================================

Running: Black (code formatting check)...
✓ Black (code formatting check) passed
Running: isort (import sorting check)...
✓ isort (import sorting check) passed

==================================================================
                      2. Code Linting
==================================================================

Running: Flake8 (critical errors check)...
✓ Flake8 (critical errors check) passed

==================================================================
                        SUMMARY
==================================================================

✓ Black                PASSED
✓ isort                PASSED
✓ Flake8               PASSED

Results: 3 passed, 0 failed

✓ ALL CHECKS PASSED! You're ready to commit and push.
```

## Need Help?

- Check the [CI/CD Setup Guide](.github/CI_CD_SETUP.md)
- Review workflow files in `.github/workflows/`
- Run individual tools for more details:
  - `python -m black --help`
  - `python -m flake8 --help`
  - `python -m bandit --help`
