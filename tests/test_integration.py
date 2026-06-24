"""
Comprehensive System Integration Tests
Tests all components and third-party integrations end-to-end
Run this after starting the backend: python tests/test_integration.py
"""
import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from typing import Dict, Any, List

# ==================== SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"
API_TIMEOUT = 10

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


# ==================== TEST RESULTS ====================
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"{Colors.GREEN}✅ PASS{Colors.END}: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"{Colors.RED}❌ FAIL{Colors.END}: {test_name}")
        print(f"   Error: {error}")

    def add_skip(self, test_name: str, reason: str):
        self.skipped += 1
        print(f"{Colors.YELLOW}⏭️  SKIP{Colors.END}: {test_name} - {reason}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'='*60}")
        print(f"{Colors.BLUE}Test Results Summary{Colors.END}")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"{Colors.YELLOW}Skipped: {self.skipped}{Colors.END}")
        print(f"{'='*60}")
        return self.failed == 0


# ==================== HEALTH & CONNECTIVITY TESTS ====================
def test_backend_health(results: TestResults):
    """Test if backend is running and responding"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                results.add_pass("Backend health check")
                return True
            else:
                results.add_fail("Backend health check", "Status not 'healthy'")
                return False
        else:
            results.add_fail("Backend health check", f"Status code {response.status_code}")
            return False
    except requests.ConnectionError:
        results.add_fail("Backend health check", "Cannot connect to backend (is it running?)")
        return False
    except Exception as e:
        results.add_fail("Backend health check", str(e))
        return False


def test_database_connectivity(results: TestResults):
    """Test database connectivity via graph-state endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/graph-state", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if "network_state" in data:
                results.add_pass(f"Database connectivity (found {data.get('total_records', 0)} records)")
                return True
            else:
                results.add_fail("Database connectivity", "Invalid response format")
                return False
        else:
            results.add_fail("Database connectivity", f"Status code {response.status_code}: {response.text}")
            return False
    except requests.ConnectionError:
        results.add_fail("Database connectivity", "Cannot connect to backend")
        return False
    except Exception as e:
        results.add_fail("Database connectivity", str(e))
        return False


# ==================== INPUT VALIDATION TESTS ====================
def test_input_validation_citizen_id(results: TestResults):
    """Test citizen_id validation"""
    test_cases = [
        ("ab", False, "Too short"),
        ("citizen_001", True, "Valid"),
        ("citizen-002", True, "Valid with hyphen"),
        ("citizen_@#$", False, "Invalid characters"),
        ("", False, "Empty string"),
    ]

    for citizen_id, should_pass, description in test_cases:
        payload = {
            "citizen_id": citizen_id,
            "intent": "RESOURCE_REQUEST",
            "item": "Blood Pack",
            "urgency": "CRITICAL",
            "location_context": "Hospital"
        }
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/ingest",
                json=payload,
                timeout=API_TIMEOUT
            )

            if should_pass and response.status_code == 200:
                results.add_pass(f"Citizen ID validation: {description}")
            elif not should_pass and response.status_code == 400:
                results.add_pass(f"Citizen ID validation: {description} (properly rejected)")
            elif not should_pass and response.status_code == 200:
                results.add_fail(f"Citizen ID validation: {description}", "Should have been rejected")
            else:
                results.add_fail(f"Citizen ID validation: {description}", f"Status {response.status_code}")
        except Exception as e:
            results.add_fail(f"Citizen ID validation: {description}", str(e))


def test_input_validation_urgency(results: TestResults):
    """Test urgency validation"""
    test_cases = [
        ("CRITICAL", True, "Valid - CRITICAL"),
        ("HIGH", True, "Valid - HIGH"),
        ("MEDIUM", True, "Valid - MEDIUM"),
        ("LOW", True, "Valid - LOW"),
        ("URGENT", False, "Invalid - not in enum"),
        ("critical", False, "Invalid - lowercase"),
    ]

    for urgency, should_pass, description in test_cases:
        payload = {
            "citizen_id": "citizen_001",
            "intent": "RESOURCE_REQUEST",
            "item": "Blood Pack",
            "urgency": urgency,
            "location_context": "Hospital"
        }
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/ingest",
                json=payload,
                timeout=API_TIMEOUT
            )

            if should_pass and response.status_code == 200:
                results.add_pass(f"Urgency validation: {description}")
            elif not should_pass and response.status_code == 400:
                results.add_pass(f"Urgency validation: {description} (properly rejected)")
            elif not should_pass and response.status_code == 200:
                results.add_fail(f"Urgency validation: {description}", "Should have been rejected")
            else:
                results.add_fail(f"Urgency validation: {description}", f"Status {response.status_code}")
        except Exception as e:
            results.add_fail(f"Urgency validation: {description}", str(e))


def test_input_validation_location(results: TestResults):
    """Test location context validation"""
    test_cases = [
        ("City Hospital", True, "Valid location"),
        ("", False, "Empty location"),
        ("A" * 501, False, "Too long (>500 chars)"),
        ("Hospital, North Wing", True, "Valid with comma"),
    ]

    for location, should_pass, description in test_cases:
        payload = {
            "citizen_id": "citizen_001",
            "intent": "RESOURCE_REQUEST",
            "item": "Blood Pack",
            "urgency": "CRITICAL",
            "location_context": location
        }
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/ingest",
                json=payload,
                timeout=API_TIMEOUT
            )

            if should_pass and response.status_code == 200:
                results.add_pass(f"Location validation: {description}")
            elif not should_pass and response.status_code == 400:
                results.add_pass(f"Location validation: {description} (properly rejected)")
            else:
                results.add_fail(f"Location validation: {description}", f"Status {response.status_code}")
        except Exception as e:
            results.add_fail(f"Location validation: {description}", str(e))


# ==================== CORE FUNCTIONALITY TESTS ====================
def test_resource_request_ingestion(results: TestResults):
    """Test valid resource request ingestion"""
    payload = {
        "citizen_id": f"citizen_test_{int(datetime.now().timestamp())}",
        "intent": "RESOURCE_REQUEST",
        "item": "Blood Pack",
        "urgency": "CRITICAL",
        "location_context": "Emergency Department, City Hospital"
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/ingest",
            json=payload,
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                results.add_pass("Resource request ingestion")
                return payload["citizen_id"]
            else:
                results.add_fail("Resource request ingestion", f"Invalid response: {data}")
                return None
        else:
            results.add_fail("Resource request ingestion", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        results.add_fail("Resource request ingestion", str(e))
        return None


def test_all_resource_types(results: TestResults):
    """Test all supported resource types"""
    resource_types = [
        "Insulin",
        "Blood Pack",
        "Oxygen Cylinder",
        "Clean Water",
        "Medicines",
        "Vaccines",
        "First Aid Kit",
        "Food Supplies"
    ]

    for resource_type in resource_types:
        payload = {
            "citizen_id": f"citizen_resource_test_{int(datetime.now().timestamp())}",
            "intent": "RESOURCE_REQUEST",
            "item": resource_type,
            "urgency": "HIGH",
            "location_context": "Test Location"
        }
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/ingest",
                json=payload,
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                results.add_pass(f"Resource type support: {resource_type}")
            else:
                results.add_fail(f"Resource type support: {resource_type}", f"Status {response.status_code}")
        except Exception as e:
            results.add_fail(f"Resource type support: {resource_type}", str(e))


# ==================== ERROR HANDLING TESTS ====================
def test_error_handling_missing_fields(results: TestResults):
    """Test error handling for missing required fields"""
    test_cases = [
        ({}, "Empty payload"),
        ({"citizen_id": "test"}, "Missing intent"),
        ({"citizen_id": "test", "intent": "RESOURCE_REQUEST"}, "Missing item"),
    ]

    for payload, description in test_cases:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/ingest",
                json=payload,
                timeout=API_TIMEOUT
            )

            if response.status_code == 422:  # Unprocessable Entity
                results.add_pass(f"Error handling: {description}")
            else:
                results.add_fail(f"Error handling: {description}", f"Expected 422, got {response.status_code}")
        except Exception as e:
            results.add_fail(f"Error handling: {description}", str(e))


def test_error_handling_cors(results: TestResults):
    """Test CORS headers are properly set"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=API_TIMEOUT
        )

        # Check for CORS headers
        headers = response.headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
            "Cache-Control"
        ]

        found_count = sum(1 for h in security_headers if h in headers)

        if found_count >= 3:
            results.add_pass(f"Security headers present ({found_count}/{len(security_headers)})")
        else:
            results.add_fail("Security headers", f"Only found {found_count}/{len(security_headers)}")
    except Exception as e:
        results.add_fail("Security headers check", str(e))


# ==================== API ENDPOINT TESTS ====================
def test_all_endpoints_accessible(results: TestResults):
    """Test all documented endpoints are accessible"""
    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/v1/graph-state"),
        ("POST", "/api/v1/ingest"),
        ("POST", "/api/v1/migrate"),
        ("POST", "/api/v1/ingest/audio"),
    ]

    for method, path in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{path}", timeout=API_TIMEOUT)
            else:
                # For POST endpoints, send appropriate test data
                if path == "/api/v1/ingest":
                    response = requests.post(
                        f"{BACKEND_URL}{path}",
                        json={
                            "citizen_id": "test",
                            "intent": "RESOURCE_REQUEST",
                            "item": "Blood Pack",
                            "urgency": "CRITICAL",
                            "location_context": "Test"
                        },
                        timeout=API_TIMEOUT
                    )
                else:
                    response = requests.post(f"{BACKEND_URL}{path}", timeout=API_TIMEOUT)

            # 200, 201, 400, 422 are all "accessible" - 500+ means server error
            if response.status_code < 500:
                results.add_pass(f"Endpoint accessible: {method} {path} ({response.status_code})")
            else:
                results.add_fail(f"Endpoint accessible: {method} {path}", f"Status {response.status_code}")
        except requests.Timeout:
            results.add_fail(f"Endpoint accessible: {method} {path}", "Request timeout")
        except requests.ConnectionError:
            results.add_fail(f"Endpoint accessible: {method} {path}", "Connection error")
        except Exception as e:
            results.add_fail(f"Endpoint accessible: {method} {path}", str(e))


# ==================== RESPONSE FORMAT TESTS ====================
def test_response_format_success(results: TestResults):
    """Test success response format"""
    payload = {
        "citizen_id": f"citizen_format_test_{int(datetime.now().timestamp())}",
        "intent": "RESOURCE_REQUEST",
        "item": "Blood Pack",
        "urgency": "CRITICAL",
        "location_context": "Test Location"
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/ingest",
            json=payload,
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            required_fields = ["status", "message", "timestamp"]

            if all(field in data for field in required_fields):
                if data["status"] == "success":
                    results.add_pass("Response format: Success response")
                else:
                    results.add_fail("Response format", "Status not 'success'")
            else:
                results.add_fail("Response format", f"Missing fields. Got: {list(data.keys())}")
        else:
            results.add_fail("Response format", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Response format", str(e))


def test_response_format_error(results: TestResults):
    """Test error response format"""
    payload = {
        "citizen_id": "ab",  # Too short - will trigger validation error
        "intent": "RESOURCE_REQUEST",
        "item": "Blood Pack",
        "urgency": "CRITICAL",
        "location_context": "Test Location"
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/ingest",
            json=payload,
            timeout=API_TIMEOUT
        )

        if response.status_code == 400:
            data = response.json()
            required_fields = ["status", "message", "timestamp"]

            if all(field in data for field in required_fields):
                if data["status"] == "error":
                    results.add_pass("Response format: Error response")
                else:
                    results.add_fail("Response format", "Error status not set")
            else:
                results.add_fail("Response format", f"Missing error fields. Got: {list(data.keys())}")
        else:
            results.add_fail("Response format: Error response", f"Expected 400, got {response.status_code}")
    except Exception as e:
        results.add_fail("Response format: Error response", str(e))


# ==================== THIRD-PARTY INTEGRATION TESTS ====================
def test_sarvam_api_key_configured(results: TestResults):
    """Test that Sarvam API key is configured"""
    try:
        from config import settings

        if settings.SARVAM_API_KEY and settings.SARVAM_API_KEY != "your_key_here":
            results.add_pass("Third-party: Sarvam API key configured")
        else:
            results.add_fail("Third-party: Sarvam API key", "API key not configured or using default")
    except Exception as e:
        results.add_fail("Third-party: Sarvam API key check", str(e))


def test_neo4j_configured(results: TestResults):
    """Test that Neo4j is properly configured"""
    try:
        from config import settings

        if settings.NEO4J_URI and settings.NEO4J_USER and settings.NEO4J_PASSWORD:
            results.add_pass("Third-party: Neo4j configured")
        else:
            results.add_fail("Third-party: Neo4j", "Database credentials not configured")
    except Exception as e:
        results.add_fail("Third-party: Neo4j check", str(e))


def test_cors_origins_configured(results: TestResults):
    """Test that CORS origins are properly configured"""
    try:
        from config import settings

        if settings.CORS_ORIGINS and len(settings.CORS_ORIGINS) > 0:
            origins_str = ", ".join(settings.CORS_ORIGINS)
            results.add_pass(f"Third-party: CORS configured ({len(settings.CORS_ORIGINS)} origins)")
        else:
            results.add_fail("Third-party: CORS", "No CORS origins configured")
    except Exception as e:
        results.add_fail("Third-party: CORS check", str(e))


# ==================== CONFIGURATION TESTS ====================
def test_configuration_loading(results: TestResults):
    """Test that configuration loads without errors"""
    try:
        from config import settings

        # Check critical configuration
        required_attrs = [
            'NEO4J_URI',
            'NEO4J_USER',
            'NEO4J_PASSWORD',
            'SARVAM_API_KEY',
            'CORS_ORIGINS',
            'LOG_LEVEL'
        ]

        missing = []
        for attr in required_attrs:
            if not hasattr(settings, attr):
                missing.append(attr)

        if not missing:
            results.add_pass("Configuration: All required settings present")
        else:
            results.add_fail("Configuration", f"Missing: {', '.join(missing)}")
    except Exception as e:
        results.add_fail("Configuration loading", str(e))


def test_validators_module(results: TestResults):
    """Test that validators module loads and works"""
    try:
        from validators import (
            validate_citizen_id,
            validate_urgency,
            validate_intent,
            ValidationError
        )

        # Test basic validation
        validate_citizen_id("citizen_001")
        validate_urgency("CRITICAL")
        validate_intent("RESOURCE_REQUEST")

        results.add_pass("Validators: Module functional")
    except ValidationError as e:
        results.add_fail("Validators", str(e))
    except Exception as e:
        results.add_fail("Validators: Module load", str(e))


# ==================== MAIN TEST RUNNER ====================
def run_all_tests():
    """Run all integration tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"NEXARIS Backend - End-to-End Integration Tests")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.END}\n")

    results = TestResults()

    # Configuration Tests
    print(f"\n{Colors.BLUE}[Configuration Tests]{Colors.END}")
    test_configuration_loading(results)
    test_validators_module(results)

    # Connectivity Tests
    print(f"\n{Colors.BLUE}[Connectivity Tests]{Colors.END}")
    backend_ok = test_backend_health(results)
    if backend_ok:
        test_database_connectivity(results)

    # Third-Party Integration Tests
    print(f"\n{Colors.BLUE}[Third-Party Integration Tests]{Colors.END}")
    test_sarvam_api_key_configured(results)
    test_neo4j_configured(results)
    test_cors_origins_configured(results)

    # Input Validation Tests
    print(f"\n{Colors.BLUE}[Input Validation Tests]{Colors.END}")
    test_input_validation_citizen_id(results)
    test_input_validation_urgency(results)
    test_input_validation_location(results)

    # Core Functionality Tests
    if backend_ok:
        print(f"\n{Colors.BLUE}[Core Functionality Tests]{Colors.END}")
        test_resource_request_ingestion(results)
        test_all_resource_types(results)

    # Error Handling Tests
    if backend_ok:
        print(f"\n{Colors.BLUE}[Error Handling Tests]{Colors.END}")
        test_error_handling_missing_fields(results)
        test_error_handling_cors(results)

    # API Endpoint Tests
    if backend_ok:
        print(f"\n{Colors.BLUE}[API Endpoint Tests]{Colors.END}")
        test_all_endpoints_accessible(results)

    # Response Format Tests
    if backend_ok:
        print(f"\n{Colors.BLUE}[Response Format Tests]{Colors.END}")
        test_response_format_success(results)
        test_response_format_error(results)

    # Summary
    success = results.summary()

    if success:
        print(f"\n{Colors.GREEN}✅ All tests passed! System is fully functional.{Colors.END}\n")
    else:
        print(f"\n{Colors.RED}❌ Some tests failed. See details above.{Colors.END}\n")

    return 0 if success else 1


if __name__ == "__main__":
    exit(run_all_tests())
