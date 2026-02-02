#!/usr/bin/env python3
"""
Script to run tests with coverage reporting.
This script will:
1. Run all tests
2. Generate coverage report
3. Display results with percentage
"""

import subprocess
import sys
import os

def run_tests_with_coverage():
    """Run pytest with coverage and display results."""
    print("=" * 70)
    print("Running tests with coverage...")
    print("=" * 70)
    print()
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=app",  # Measure coverage for app directory
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html",  # Generate HTML report
        "--cov-report=json",  # Generate JSON for programmatic access
        "-v",  # Verbose output
        "--tb=short",  # Shorter traceback format
    ]
    
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        print("\n" + "=" * 70)
        print("Coverage HTML report generated in: htmlcov/index.html")
        print("Coverage JSON report generated in: coverage.json")
        print("=" * 70)
        
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = run_tests_with_coverage()
    sys.exit(exit_code)
