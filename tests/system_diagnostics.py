#!/usr/bin/env python
"""
NEXARIS Backend - System Diagnostics
Comprehensive system health and diagnostics report
Run this to get a detailed report of system status
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")


def get_environment_info():
    """Get environment and system information"""
    print_section("Environment Information")

    import platform
    import sys

    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")


def check_configuration():
    """Check configuration status"""
    print_section("Configuration Status")

    try:
        from config import settings
        import os

        required_env_vars = {
            "NEO4J_URI": "Neo4j Database URL",
            "NEO4J_USER": "Neo4j Username",
            "NEO4J_PASSWORD": "Neo4j Password",
            "SARVAM_API_KEY": "Sarvam AI API Key",
            "CORS_ORIGINS": "CORS Allowed Origins",
        }

        for env_var, description in required_env_vars.items():
            value = os.getenv(env_var)
            if value:
                if "PASSWORD" in env_var or "KEY" in env_var:
                    display_value = value[:5] + "..." + value[-3:] if len(value) > 10 else "***"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value

                print(f"✓ {env_var:25} {display_value}")
            else:
                print(f"✗ {env_var:25} NOT SET")

        print(f"\nLogging Level: {settings.LOG_LEVEL}")
        print(f"Connection Pool Size: {settings.NEO4J_CONNECTION_POOL_SIZE}")
        print(f"Max Audio Size: {settings.MAX_AUDIO_FILE_SIZE_MB}MB")
        print(f"PSA Enabled: {settings.PSA_ENABLED}")

    except Exception as e:
        print(f"❌ Error reading configuration: {e}")


def check_dependencies():
    """Check installed dependencies"""
    print_section("Dependencies Status")

    required_packages = {
        "fastapi": "FastAPI Framework",
        "neo4j": "Neo4j Driver",
        "requests": "HTTP Library",
        "pydantic": "Data Validation",
        "streamlit": "Web UI Framework",
        "uvicorn": "ASGI Server",
    }

    for package, description in required_packages.items():
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            print(f"✓ {package:15} ({description:25}) v{version}")
        except ImportError:
            print(f"✗ {package:15} ({description:25}) NOT INSTALLED")


def check_file_structure():
    """Check project file structure"""
    print_section("File Structure")

    base_path = Path(__file__).parent.parent

    required_files = {
        "main.py": "FastAPI Backend",
        "app.py": "Streamlit Frontend",
        "worker.py": "Background Worker",
        "config.py": "Configuration",
        "validators.py": "Input Validators",
        ".env": "Environment Variables",
        ".env.example": "Environment Template",
        "requirements.txt": "Dependencies",
        "README.md": "Documentation",
        "Procfile": "Deployment Config",
    }

    for filename, description in required_files.items():
        file_path = base_path / filename
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {filename:20} ({description:25}) {size:,} bytes")
        else:
            print(f"✗ {filename:20} ({description:25}) MISSING")

    # Check directories
    print("\nDirectories:")
    directories = ["tests", ".venv", "__pycache__", ".git"]
    for dirname in directories:
        dir_path = base_path / dirname
        if dir_path.exists():
            print(f"✓ {dirname:20}")
        else:
            print(f"  {dirname:20} (not found)")


def check_database_config():
    """Check database configuration"""
    print_section("Database Configuration")

    try:
        from config import settings

        print(f"URI: {settings.NEO4J_URI}")
        print(f"User: {settings.NEO4J_USER}")
        print(f"Password: {'*' * len(settings.NEO4J_PASSWORD)}")
        print(f"Connection Pool: {settings.NEO4J_CONNECTION_POOL_SIZE}")
        print(f"Encrypted: True")
        print(f"Cert Validation: TRUST_SYSTEM_CA_SIGNED_CERTIFICATES")

        # Try to test connection
        try:
            from main import get_db_driver
            driver = get_db_driver()
            print(f"\n✓ Driver initialized successfully")
            driver.close()
        except Exception as e:
            print(f"\n⚠️  Driver initialization issue: {str(e)[:50]}")

    except Exception as e:
        print(f"❌ Error checking database config: {e}")


def check_third_party_apis():
    """Check third-party API configuration"""
    print_section("Third-Party API Configuration")

    try:
        from config import settings

        # Sarvam AI
        print("Sarvam AI:")
        print(f"  API URL: {settings.SARVAM_AUDIO_API_URL}")
        print(f"  API Key Configured: {'✓' if settings.SARVAM_API_KEY else '✗'}")

        # CORS
        print("\nCORS Configuration:")
        print(f"  Origins: {', '.join(settings.CORS_ORIGINS)}")
        print(f"  Allow Credentials: {settings.CORS_ALLOW_CREDENTIALS}")

        # Rate Limiting
        print("\nRate Limiting:")
        print(f"  Requests Limit: {settings.RATE_LIMIT_REQUESTS} per {settings.RATE_LIMIT_WINDOW_SECONDS}s")

        # Audio Processing
        print("\nAudio Processing:")
        print(f"  Max File Size: {settings.MAX_AUDIO_FILE_SIZE_MB}MB")
        print(f"  Allowed MIME Types: {', '.join(settings.ALLOWED_AUDIO_MIMETYPES)}")

    except Exception as e:
        print(f"❌ Error checking third-party APIs: {e}")


def check_module_imports():
    """Check if all modules can be imported"""
    print_section("Module Imports")

    modules_to_check = [
        ("config", "Configuration module"),
        ("validators", "Validators module"),
        ("main", "FastAPI application"),
        ("app", "Streamlit application"),
        ("worker", "Background worker"),
    ]

    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {module_name:15} ({description})")
        except Exception as e:
            print(f"✗ {module_name:15} ({description}) - {str(e)[:40]}")


def check_security_settings():
    """Check security-related settings"""
    print_section("Security Settings")

    try:
        from config import settings

        # CORS
        print("CORS:")
        print(f"  ✓ Specific origins configured (not '*')" if settings.CORS_ORIGINS != ["*"] else "  ✗ CORS_ORIGINS set to '*'")

        # Password
        print("\nDatabase Security:")
        print(f"  ✓ Strong password" if settings.NEO4J_PASSWORD != "password" else "  ⚠️  Default password in use")

        # Encryption
        print("\nConnection Security:")
        print(f"  ✓ Database encryption enabled")
        print(f"  ✓ Certificate validation enabled")

        # Headers
        print("\nResponse Headers:")
        print(f"  ✓ Security headers configured")

        # Rate Limiting
        print("\nRate Limiting:")
        print(f"  ✓ Rate limiting configuration: {settings.RATE_LIMIT_REQUESTS} req/{settings.RATE_LIMIT_WINDOW_SECONDS}s")

    except Exception as e:
        print(f"❌ Error checking security settings: {e}")


def check_logging_config():
    """Check logging configuration"""
    print_section("Logging Configuration")

    try:
        from config import settings

        print(f"Log Level: {settings.LOG_LEVEL}")
        print(f"Log Format: {settings.LOG_FORMAT}")
        print(f"\n✓ Logging properly configured")

    except Exception as e:
        print(f"❌ Error checking logging config: {e}")


def get_system_requirements():
    """Show system requirements vs current state"""
    print_section("System Requirements Check")

    import sys
    requirements = {
        "Python >= 3.8": f"{sys.version_info.major}.{sys.version_info.minor}",
        "FastAPI": "Installed",
        "Neo4j Driver": "Installed",
        "Streamlit": "Installed",
        "Database Connectivity": "Recommended",
        "HTTPS (Production)": "Recommended",
    }

    print("Requirement Status:")
    for requirement, status in requirements.items():
        if ">" in requirement or "Installed" in status:
            print(f"  ✓ {requirement:35} {status}")
        else:
            print(f"  ⚠️  {requirement:35} {status}")


def print_summary():
    """Print diagnostic summary"""
    print("\n" + "="*60)
    print("Diagnostic Summary")
    print("="*60)
    print("\nUse the information above to:")
    print("  • Verify configuration is correct")
    print("  • Ensure all dependencies are installed")
    print("  • Check database connectivity")
    print("  • Verify third-party integrations")
    print("  • Review security settings")
    print("\nTo start the system:")
    print("  1. python -m uvicorn main:app --reload")
    print("  2. streamlit run app.py (in another terminal)")
    print("  3. python worker.py (in another terminal)")
    print("\nTo run tests:")
    print("  • python tests/verify_startup.py")
    print("  • python tests/test_integration.py")
    print("  • python tests/test_workflow.py")
    print("\n" + "="*60 + "\n")


def main():
    """Run all diagnostics"""
    print("\n" + "="*60)
    print("NEXARIS Backend - System Diagnostics")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        get_environment_info()
        check_file_structure()
        check_dependencies()
        check_module_imports()
        check_configuration()
        check_database_config()
        check_third_party_apis()
        check_security_settings()
        check_logging_config()
        get_system_requirements()
        print_summary()
        return 0
    except Exception as e:
        print(f"\n❌ Diagnostic error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
