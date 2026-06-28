#!/usr/bin/env python
"""
NEXARIS Backend - System Startup Verification
Verifies all components start correctly and are ready for operation
Run this script to check if the entire system can start without errors.
"""
import sys
import os
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class StartupVerifier:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_skipped = 0
        self.errors = []

    def check(self, name: str, condition: bool, error_msg: str = ""):
        """Record a startup check result"""
        if condition:
            self.checks_passed += 1
            print(f"✅ {name}")
        else:
            self.checks_failed += 1
            self.errors.append((name, error_msg))
            print(f"❌ {name}")
            if error_msg:
                print(f"   Error: {error_msg}")

    def skip(self, name: str, reason: str):
        """Skip a startup check"""
        self.checks_skipped += 1
        print(f"⏭️  {name} - {reason}")

    def summary(self):
        """Print startup verification summary"""
        total = self.checks_passed + self.checks_failed + self.checks_skipped
        print(f"\n{'='*60}")
        print(f"Startup Verification Summary")
        print(f"{'='*60}")
        print(f"Total Checks: {total}")
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⏭️  Skipped: {self.checks_skipped}")
        print(f"{'='*60}")
        return self.checks_failed == 0


def verify_python_version(verifier: StartupVerifier):
    """Verify Python version is 3.8+"""
    print("\n[Python Version]")
    version_info = sys.version_info
    is_valid = version_info.major >= 3 and version_info.minor >= 8
    verifier.check(
        f"Python {version_info.major}.{version_info.minor} (>= 3.8)",
        is_valid,
        f"Requires Python 3.8 or higher, found {version_info.major}.{version_info.minor}"
    )


def verify_dependencies(verifier: StartupVerifier):
    """Verify all required dependencies can be imported"""
    print("\n[Dependencies]")

    dependencies = {
        "fastapi": "FastAPI web framework",
        "neo4j": "Neo4j database driver",
        "requests": "HTTP library",
        "pydantic": "Data validation",
        "streamlit": "Streamlit frontend",
    }

    for module_name, description in dependencies.items():
        try:
            __import__(module_name)
            verifier.check(f"{module_name} ({description})", True)
        except ImportError as e:
            verifier.check(
                f"{module_name} ({description})",
                False,
                f"Module not found: {e}"
            )


def verify_configuration(verifier: StartupVerifier):
    """Verify configuration can be loaded"""
    print("\n[Configuration]")

    try:
        from config import settings

        # Check critical configuration
        verifier.check(
            "NEO4J_URI configured",
            bool(settings.NEO4J_URI),
            "NEO4J_URI environment variable not set"
        )

        verifier.check(
            "NEO4J_USER configured",
            bool(settings.NEO4J_USER),
            "NEO4J_USER environment variable not set"
        )

        verifier.check(
            "NEO4J_PASSWORD configured",
            bool(settings.NEO4J_PASSWORD),
            "NEO4J_PASSWORD environment variable not set"
        )

        verifier.check(
            "SARVAM_API_KEY configured",
            bool(settings.SARVAM_API_KEY),
            "SARVAM_API_KEY environment variable not set"
        )

        verifier.check(
            "CORS_ORIGINS configured",
            bool(settings.CORS_ORIGINS and len(settings.CORS_ORIGINS) > 0),
            "CORS_ORIGINS not configured"
        )

        verifier.check(
            "Passwords not using weak defaults",
            settings.NEO4J_PASSWORD != "password",
            "Warning: Using default password 'password' - not secure for production"
        )

    except ValueError as e:
        verifier.check("Configuration loading", False, str(e))
    except Exception as e:
        verifier.check("Configuration loading", False, str(e))


def verify_modules(verifier: StartupVerifier):
    """Verify custom modules can be imported"""
    print("\n[Custom Modules]")

    try:
        from validators import (
            validate_citizen_id,
            validate_urgency,
            validate_intent,
            validate_resource_type,
            validate_location_context,
            ValidationError,
        )
        verifier.check("validators module", True)
    except Exception as e:
        verifier.check("validators module", False, str(e))

    try:
        from config import settings
        verifier.check("config module", True)
    except Exception as e:
        verifier.check("config module", False, str(e))


def verify_database_driver(verifier: StartupVerifier):
    """Verify database driver can be initialized"""
    print("\n[Database Driver]")

    try:
        from db import get_db_driver
        from config import settings

        # Try to create driver (but don't verify connectivity - might not be available)
        try:
            driver = get_db_driver()
            verifier.check("Neo4j driver initialization", True)
            if driver:
                driver.close()
        except Exception as e:
            # Database might not be running, but driver should initialize
            verifier.skip(
                "Neo4j driver connectivity",
                f"Database not running or unreachable: {str(e)[:50]}"
            )
    except Exception as e:
        verifier.check("Neo4j driver initialization", False, str(e))


def verify_fastapi_app(verifier: StartupVerifier):
    """Verify FastAPI app can be initialized"""
    print("\n[FastAPI Application]")

    try:
        from main import app

        # Check app is configured correctly
        verifier.check("FastAPI app initialization", True)

        # Check app has expected routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/api/v1/ingest", "/api/v1/graph-state"]

        for route in expected_routes:
            verifier.check(f"Route {route} available", route in routes)
    except Exception as e:
        verifier.check("FastAPI app initialization", False, str(e))


def verify_streamlit_app(verifier: StartupVerifier):
    """Verify Streamlit app can be loaded"""
    print("\n[Streamlit Application]")

    app_path = Path(__file__).parent.parent / "app.py"

    try:
        with open(app_path, 'r') as f:
            content = f.read()

        required_imports = ["streamlit", "requests"]
        all_present = all(f"import {imp}" in content or f"from {imp}" in content
                         for imp in required_imports)

        verifier.check("Streamlit app file", app_path.exists() and all_present)
    except Exception as e:
        verifier.check("Streamlit app file", False, str(e))


def verify_worker_process(verifier: StartupVerifier):
    """Verify background worker can be initialized"""
    print("\n[Background Worker]")

    worker_path = Path(__file__).parent.parent / "worker.py"

    try:
        with open(worker_path, 'r') as f:
            content = f.read()

        # Check for key components
        has_get_db_driver = "get_db_driver" in content
        has_durable_loop = "def durable_agent_loop()" in content
        has_main = "if __name__" in content

        verifier.check("Worker file exists and valid",
                      worker_path.exists() and has_get_db_driver and has_durable_loop and has_main)
    except Exception as e:
        verifier.check("Worker file", False, str(e))


def verify_environment_file(verifier: StartupVerifier):
    """Verify .env file exists"""
    print("\n[Environment File]")

    env_path = Path(__file__).parent.parent / ".env"
    env_example_path = Path(__file__).parent.parent / ".env.example"

    if env_path.exists():
        verifier.check(".env file exists", True)
    elif env_example_path.exists():
        verifier.skip(".env file", "Use: cp .env.example .env")
    else:
        verifier.check(".env file exists", False, "Neither .env nor .env.example found")


def verify_requirements(verifier: StartupVerifier):
    """Verify requirements.txt exists and is valid"""
    print("\n[Requirements]")

    req_path = Path(__file__).parent.parent / "requirements.txt"

    try:
        if req_path.exists():
            with open(req_path, 'r') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]

            verifier.check(
                f"requirements.txt ({len(lines)} dependencies)",
                len(lines) > 10,
                "requirements.txt appears to be missing dependencies"
            )
        else:
            verifier.check("requirements.txt exists", False, "File not found")
    except Exception as e:
        verifier.check("requirements.txt", False, str(e))


def verify_documentation(verifier: StartupVerifier):
    """Verify documentation files exist"""
    print("\n[Documentation]")

    docs = {
        "README.md": "Main documentation",
        ".env.example": "Environment template",
        "SECURITY_AUDIT.md": "Security audit report",
        "QUICK_START.md": "Quick start guide",
    }

    base_path = Path(__file__).parent.parent

    for doc_file, description in docs.items():
        doc_path = base_path / doc_file
        verifier.check(f"{doc_file} ({description})", doc_path.exists())


def main():
    """Run all startup verification checks"""
    print("="*60)
    print("NEXARIS Backend - Startup Verification")
    print("="*60)

    verifier = StartupVerifier()

    try:
        verify_python_version(verifier)
        verify_dependencies(verifier)
        verify_configuration(verifier)
        verify_modules(verifier)
        verify_database_driver(verifier)
        verify_fastapi_app(verifier)
        verify_streamlit_app(verifier)
        verify_worker_process(verifier)
        verify_environment_file(verifier)
        verify_requirements(verifier)
        verify_documentation(verifier)
    except Exception as e:
        print(f"\n❌ Unexpected error during verification:")
        print(traceback.format_exc())

    success = verifier.summary()

    if success:
        print(f"\n✅ All startup checks passed! System is ready to start.")
        print(f"\nNext steps:")
        print(f"  1. python -m uvicorn main:app --reload")
        print(f"  2. streamlit run app.py (in another terminal)")
        print(f"  3. python worker.py (in another terminal)")
    else:
        print(f"\n❌ Some startup checks failed. Please review the errors above.")
        if verifier.errors:
            print(f"\nFailed checks:")
            for check_name, error in verifier.errors:
                print(f"  • {check_name}: {error}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
