#!/usr/bin/env python
"""
NEXARIS Backend - Master Test Runner
Coordinates all tests and provides comprehensive system verification
Run this to execute the complete test suite
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import time

# Test files available
TESTS = {
    "startup": {
        "file": "verify_startup.py",
        "description": "Startup verification (pre-flight checks)",
        "time": "2-3 min"
    },
    "diagnostics": {
        "file": "system_diagnostics.py",
        "description": "System diagnostics and configuration report",
        "time": "2-3 min"
    },
    "integration": {
        "file": "test_integration.py",
        "description": "Integration tests (all components + third-party)",
        "time": "5-10 min",
        "requires_backend": True
    },
    "workflow": {
        "file": "test_workflow.py",
        "description": "End-to-end workflow tests",
        "time": "5-10 min",
        "requires_backend": True
    },
    "unit": {
        "file": "test_validators.py",
        "description": "Unit tests for individual components (e.g., validators)",
        "time": "< 1 min"
    },
}


def print_header():
    """Print test runner header"""
    print("\n" + "="*70)
    print("🧪 NEXARIS Backend - Master Test Runner")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def print_menu():
    """Print test menu"""
    print("Available Tests:")
    print("-" * 70)
    for idx, (key, test) in enumerate(TESTS.items(), 1):
        backend_req = " (requires backend running)" if test.get("requires_backend") else ""
        print(f"{idx}. {key.upper():15} - {test['description']}{backend_req}")
        print(f"   Estimated time: {test['time']}")
    print("-" * 70)


def run_test(test_key: str, test_file: str) -> bool:
    """Run a single test"""
    test_path = Path(__file__).parent / test_file

    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    print(f"\n{'='*70}")
    print(f"Running: {test_key.upper()}")
    print(f"File: {test_file}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*70}\n")

    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=Path(__file__).parent.parent
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def run_all_tests() -> bool:
    """Run all tests in sequence"""
    print("\n📋 Running all tests...\n")

    results = {}
    start_time = time.time()

    for key, test in TESTS.items():
        if test.get("requires_backend"):
            print(f"⏭️  Skipping {key} - requires backend running")
            results[key] = "skipped"
            continue

        success = run_test(key, test["file"])
        results[key] = "passed" if success else "failed"
        time.sleep(1)  # Brief pause between tests

    # Print summary
    print_summary(results, time.time() - start_time)
    return all(v == "passed" or v == "skipped" for v in results.values())


def print_summary(results: dict, elapsed_time: float):
    """Print test summary"""
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)

    passed = sum(1 for v in results.values() if v == "passed")
    failed = sum(1 for v in results.values() if v == "failed")
    skipped = sum(1 for v in results.values() if v == "skipped")
    total = len(results)

    print(f"\nResults:")
    for test_name, status in results.items():
        icon = "✅" if status == "passed" else "❌" if status == "failed" else "⏭️"
        print(f"  {icon} {test_name.upper():15} {status.upper()}")

    print(f"\nStatistics:")
    print(f"  Total Tests: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  Time Elapsed: {elapsed_time:.1f} seconds")

    print("\n" + "="*70)


def print_instructions():
    """Print testing instructions"""
    print("\n" + "="*70)
    print("📚 Complete Testing Workflow")
    print("="*70)
    print("""
1. PRE-FLIGHT CHECKS (Run first):
   python tests/verify_startup.py

   • Verifies Python version, dependencies, configuration
   • Must pass before starting services

2. SYSTEM DIAGNOSTICS (Optional but recommended):
   python tests/system_diagnostics.py

   • Get comprehensive system status
   • Verify all configurations are correct

3. START BACKEND (Terminal 1):
   python -m uvicorn main:app --reload

   • Wait for: "Application startup complete"
   • Keep running while testing

4. RUN INTEGRATION TESTS (Terminal 2):
   python tests/test_integration.py

   • Tests all components and third-party integrations
   • Requires backend running

5. RUN WORKFLOW TESTS (Terminal 2):
   python tests/test_workflow.py

   • Tests complete end-to-end workflow
   • Requires backend running

6. START STREAMLIT (Terminal 3, Optional):
   streamlit run app.py

   • Opens UI at http://localhost:8501
   • Manual testing available

7. START WORKER (Terminal 4, Optional):
   python worker.py

   • Starts background PSA agent
   • Processes requests autonomously
""")
    print("="*70)


def main():
    """Main test runner"""
    print_header()

    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "all":
            success = run_all_tests()
            sys.exit(0 if success else 1)

        elif command in TESTS:
            success = run_test(command, TESTS[command]["file"])
            sys.exit(0 if success else 1)

        elif command == "help":
            print_menu()
            print_instructions()
            sys.exit(0)

        else:
            print(f"Unknown command: {command}")
            print("Use: python run_tests.py [startup|diagnostics|integration|workflow|all|help]")
            sys.exit(1)

    # Interactive menu
    print_menu()
    print_instructions()

    print("\nUsage:")
    print("  python run_tests.py startup       - Run startup verification")
    print("  python run_tests.py diagnostics   - Run system diagnostics")
    print("  python run_tests.py integration   - Run integration tests")
    print("  python run_tests.py workflow      - Run workflow tests")
    print("  python run_tests.py unit          - Run unit tests")
    print("  python run_tests.py all           - Run all non-backend tests")
    print("  python run_tests.py help          - Show this help message\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test runner interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
