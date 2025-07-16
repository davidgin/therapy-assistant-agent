#!/usr/bin/env python3
"""
Test runner script for therapy-assistant-agent
Provides convenient commands for running different types of tests
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result."""
    if description:
        print(f"\n🧪 {description}")
        print("=" * 50)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description or 'Command'} completed successfully")
        return True


def run_unit_tests(verbose=False, coverage=True):
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    cmd.append("-m")
    cmd.append("unit")
    
    return run_command(cmd, "Running Unit Tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("-m")
    cmd.append("integration")
    
    return run_command(cmd, "Running Integration Tests")


def run_all_tests(verbose=False, coverage=True):
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
    
    return run_command(cmd, "Running All Tests")


def run_specific_tests(test_path, verbose=False):
    """Run specific test file or directory."""
    cmd = ["python", "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Running Tests: {test_path}")


def run_tests_by_marker(marker, verbose=False):
    """Run tests with specific marker."""
    cmd = ["python", "-m", "pytest", "-m", marker, "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Running Tests with Marker: {marker}")


def run_failed_tests():
    """Run only failed tests from last run."""
    cmd = ["python", "-m", "pytest", "--lf", "tests/"]
    
    return run_command(cmd, "Running Failed Tests from Last Run")


def run_coverage_report():
    """Generate coverage report."""
    cmd = ["python", "-m", "pytest", "--cov=app", "--cov-report=html", "--cov-report=term", "tests/"]
    
    return run_command(cmd, "Generating Coverage Report")


def run_performance_tests():
    """Run performance tests."""
    cmd = ["python", "-m", "pytest", "-m", "performance", "tests/"]
    
    return run_command(cmd, "Running Performance Tests")


def run_security_tests():
    """Run security tests."""
    cmd = ["python", "-m", "pytest", "-m", "security", "tests/"]
    
    return run_command(cmd, "Running Security Tests")


def check_test_environment():
    """Check if test environment is properly set up."""
    print("🔍 Checking Test Environment")
    print("=" * 50)
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest is installed (version: {pytest.__version__})")
    except ImportError:
        print("❌ pytest is not installed")
        return False
    
    # Check if required test dependencies are installed
    required_packages = [
        'pytest-asyncio',
        'pytest-cov',
        'httpx',
        'fastapi',
        'sqlalchemy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    # Check if test files exist
    test_files = [
        "tests/conftest.py",
        "tests/unit/test_auth_endpoints.py",
        "tests/unit/test_audio_analysis.py",
        "tests/unit/test_web_routes.py",
        "tests/unit/test_voice_endpoints.py",
        "tests/unit/test_database_models.py",
        "tests/unit/test_utility_functions.py",
        "tests/integration/test_api_integration.py"
    ]
    
    missing_files = []
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✅ {test_file} exists")
        else:
            missing_files.append(test_file)
            print(f"❌ {test_file} is missing")
    
    if missing_files:
        print(f"\n⚠️  Missing test files: {', '.join(missing_files)}")
        return False
    
    print("\n✅ Test environment is properly configured!")
    return True


def clean_test_artifacts():
    """Clean test artifacts and cache files."""
    print("🧹 Cleaning Test Artifacts")
    print("=" * 50)
    
    artifacts = [
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "coverage.xml",
        "__pycache__",
        "*.pyc"
    ]
    
    for artifact in artifacts:
        if artifact.endswith("*"):
            # Handle glob patterns
            import glob
            for file in glob.glob(f"**/{artifact}", recursive=True):
                try:
                    os.remove(file)
                    print(f"🗑️  Removed {file}")
                except OSError:
                    pass
        else:
            # Handle directories and files
            if Path(artifact).exists():
                import shutil
                if Path(artifact).is_dir():
                    shutil.rmtree(artifact)
                    print(f"🗑️  Removed directory {artifact}")
                else:
                    os.remove(artifact)
                    print(f"🗑️  Removed file {artifact}")
    
    print("✅ Cleanup completed!")


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Test runner for therapy-assistant-agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit                 # Run unit tests
  python run_tests.py --integration          # Run integration tests
  python run_tests.py --all                  # Run all tests
  python run_tests.py --marker auth          # Run auth tests
  python run_tests.py --file tests/unit/test_auth_endpoints.py
  python run_tests.py --failed               # Run failed tests
  python run_tests.py --coverage             # Generate coverage report
  python run_tests.py --check                # Check test environment
  python run_tests.py --clean                # Clean test artifacts
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--marker", type=str, help="Run tests with specific marker")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--failed", action="store_true", help="Run only failed tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--check", action="store_true", help="Check test environment")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success = True
    
    if args.check:
        success = check_test_environment()
    elif args.clean:
        clean_test_artifacts()
    elif args.unit:
        success = run_unit_tests(args.verbose, not args.no_coverage)
    elif args.integration:
        success = run_integration_tests(args.verbose)
    elif args.all:
        success = run_all_tests(args.verbose, not args.no_coverage)
    elif args.marker:
        success = run_tests_by_marker(args.marker, args.verbose)
    elif args.file:
        success = run_specific_tests(args.file, args.verbose)
    elif args.failed:
        success = run_failed_tests()
    elif args.coverage:
        success = run_coverage_report()
    elif args.performance:
        success = run_performance_tests()
    elif args.security:
        success = run_security_tests()
    else:
        print("❌ No valid option specified. Use --help for usage information.")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()