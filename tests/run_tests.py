#!/usr/bin/env python3
"""
Test Runner for Home Assistant

Provides convenient commands to run different test suites:
- Unit tests: Fast tests with no external dependencies
- Integration tests: Tests that require external services (AI, speech, hardware)
"""

import sys
import os
import subprocess
import argparse

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


def run_unit_tests(verbose=False):
    """Run unit tests only (no external dependencies)."""
    print("🧪 Running Unit Tests")
    print("=" * 40)
    print("These tests run quickly and don't require external services")
    print()
    
    verbosity = ["-v"] if verbose else []
    cmd = ["python3", "-m", "unittest", "discover", "tests/unit/"] + verbosity
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print("✅ Unit tests passed!")
        else:
            print("⚠️  Some unit tests failed (possibly due to missing optional dependencies)")
            print("   This is expected if you haven't installed all dependencies")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False


def run_integration_tests(verbose=False):
    """Run integration tests (require external services)."""
    print("🔗 Running Integration Tests")
    print("=" * 40)
    print("These tests require external services and may take longer")
    print("Required: AI API keys, microphone, speakers")
    print()
    
    verbosity = "-v" if verbose else ""
    cmd = ["python3", "-m", "unittest", "discover", "tests/integration/", verbosity]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False


def run_all_tests(verbose=False):
    """Run all tests."""
    print("🔬 Running All Tests")
    print("=" * 40)
    
    unit_success = run_unit_tests(verbose)
    print()
    integration_success = run_integration_tests(verbose)
    
    print(f"\n{'='*20} Test Summary {'='*20}")
    unit_status = "✅ PASS" if unit_success else "❌ FAIL"
    integration_status = "✅ PASS" if integration_success else "❌ FAIL"
    
    print(f"Unit Tests: {unit_status}")
    print(f"Integration Tests: {integration_status}")
    
    if unit_success and integration_success:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed.")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    required_modules = [
        ('yaml', 'PyYAML', 'pip install PyYAML'),
        ('pyttsx3', 'pyttsx3', 'pip install pyttsx3'),
        ('speech_recognition', 'SpeechRecognition', 'pip install SpeechRecognition'),
        ('anthropic', 'anthropic', 'pip install anthropic'),
        ('openai', 'openai', 'pip install openai'),
    ]
    
    missing = []
    
    for module, name, install_cmd in required_modules:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - Install with: {install_cmd}")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Unit tests may still work, but integration tests will fail.")
        return False
    else:
        print("✅ All dependencies available!")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Home Assistant tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py                 # Run all tests
  python tests/run_tests.py --unit          # Run only unit tests
  python tests/run_tests.py --integration   # Run only integration tests
  python tests/run_tests.py --deps          # Check dependencies
  python tests/run_tests.py --unit -v       # Run unit tests with verbose output
        """
    )
    
    parser.add_argument('--unit', action='store_true', 
                       help='Run unit tests only (fast, no external dependencies)')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests only (require external services)')
    parser.add_argument('--deps', action='store_true',
                       help='Check required dependencies')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    elif args.unit:
        success = run_unit_tests(args.verbose)
        sys.exit(0 if success else 1)
    elif args.integration:
        success = run_integration_tests(args.verbose)
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests(args.verbose)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()