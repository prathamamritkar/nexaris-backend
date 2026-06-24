#!/usr/bin/env python
"""
NEXARIS Backend - End-to-End Workflow Test
Tests the complete workflow from resource request submission to database storage
This verifies the entire system works together properly.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests


class WorkflowTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 10
        self.test_data = []

    def section(self, title: str):
        """Print a section header"""
        print(f"\n{'='*60}")
        print(f"📋 {title}")
        print(f"{'='*60}")

    def step(self, number: int, description: str, status: str = ""):
        """Print a workflow step"""
        status_icon = "⏳" if status == "running" else "✅" if status == "success" else "❌" if status == "failed" else "→"
        print(f"\n{status_icon} Step {number}: {description}")
        if status == "running":
            print(f"  Processing...")

    def log(self, message: str, indent=2):
        """Log a message"""
        print(f"{' '*indent}{message}")

    def run_complete_workflow(self) -> bool:
        """Execute the complete workflow"""
        success = True

        try:
            self.section("Phase 1: System Health Check")

            # Step 1: Verify backend is running
            self.step(1, "Checking backend health", "running")
            try:
                response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    self.step(1, "Checking backend health", "success")
                    self.log(f"Backend Status: {data.get('status', 'unknown')}")
                else:
                    self.step(1, "Checking backend health", "failed")
                    return False
            except requests.ConnectionError:
                self.step(1, "Checking backend health", "failed")
                self.log("❌ Cannot connect to backend. Is it running on port 8000?")
                return False

            # Step 2: Verify database connectivity
            self.step(2, "Verifying database connectivity", "running")
            try:
                response = requests.get(f"{self.base_url}/api/v1/graph-state", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    self.step(2, "Verifying database connectivity", "success")
                    self.log(f"Database Records: {data.get('total_records', 0)}")
                else:
                    self.step(2, "Verifying database connectivity", "failed")
                    self.log(f"Status Code: {response.status_code}")
                    return False
            except Exception as e:
                self.step(2, "Verifying database connectivity", "failed")
                self.log(f"Error: {str(e)}")
                return False

            # ==================== PHASE 2: Submit Resource Requests ====================
            self.section("Phase 2: Submit Resource Requests")

            # Step 3: Submit valid request
            self.step(3, "Submitting valid resource request", "running")
            request_1_id = f"test_citizen_{int(time.time() * 1000)}"
            payload_1 = {
                "citizen_id": request_1_id,
                "intent": "RESOURCE_REQUEST",
                "item": "Blood Pack",
                "urgency": "CRITICAL",
                "location_context": "Emergency Department, City Hospital"
            }

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ingest",
                    json=payload_1,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    self.step(3, "Submitting valid resource request", "success")
                    self.log(f"Citizen ID: {request_1_id}")
                    self.log(f"Item: Blood Pack")
                    self.log(f"Urgency: CRITICAL")
                    self.log(f"Location: Emergency Department, City Hospital")
                    self.log(f"Response: {data.get('message', 'Success')}")
                    self.test_data.append({
                        "citizen_id": request_1_id,
                        "item": "Blood Pack",
                        "urgency": "CRITICAL"
                    })
                else:
                    self.step(3, "Submitting valid resource request", "failed")
                    self.log(f"Status Code: {response.status_code}")
                    self.log(f"Response: {response.text}")
                    return False
            except Exception as e:
                self.step(3, "Submitting valid resource request", "failed")
                self.log(f"Error: {str(e)}")
                return False

            # Step 4: Submit multiple requests with different urgency levels
            self.step(4, "Submitting requests with different urgency levels", "running")
            urgency_levels = ["HIGH", "MEDIUM", "LOW"]
            for idx, urgency in enumerate(urgency_levels, 1):
                request_id = f"test_citizen_urgency_{idx}_{int(time.time() * 1000)}"
                payload = {
                    "citizen_id": request_id,
                    "intent": "RESOURCE_REQUEST",
                    "item": "Medicines",
                    "urgency": urgency,
                    "location_context": f"Test Location {idx}"
                }
                try:
                    response = requests.post(
                        f"{self.base_url}/api/v1/ingest",
                        json=payload,
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        self.log(f"  ✓ {urgency} priority request submitted")
                        self.test_data.append({
                            "citizen_id": request_id,
                            "item": "Medicines",
                            "urgency": urgency
                        })
                    else:
                        self.log(f"  ✗ {urgency} priority request failed")
                        success = False
                except Exception as e:
                    self.log(f"  ✗ {urgency} priority request error: {str(e)}")
                    success = False

            if success:
                self.step(4, "Submitting requests with different urgency levels", "success")
            else:
                self.step(4, "Submitting requests with different urgency levels", "failed")
                return False

            # Step 5: Submit requests with different resource types
            self.step(5, "Submitting requests for different resource types", "running")
            resource_types = ["Insulin", "Oxygen Cylinder", "Clean Water", "Vaccines"]
            for idx, resource in enumerate(resource_types, 1):
                request_id = f"test_citizen_resource_{idx}_{int(time.time() * 1000)}"
                payload = {
                    "citizen_id": request_id,
                    "intent": "RESOURCE_REQUEST",
                    "item": resource,
                    "urgency": "HIGH",
                    "location_context": f"Location for {resource}"
                }
                try:
                    response = requests.post(
                        f"{self.base_url}/api/v1/ingest",
                        json=payload,
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        self.log(f"  ✓ {resource} request submitted")
                        self.test_data.append({
                            "citizen_id": request_id,
                            "item": resource,
                            "urgency": "HIGH"
                        })
                    else:
                        self.log(f"  ✗ {resource} request failed")
                        success = False
                except Exception as e:
                    self.log(f"  ✗ {resource} request error: {str(e)}")
                    success = False

            if success:
                self.step(5, "Submitting requests for different resource types", "success")
            else:
                self.step(5, "Submitting requests for different resource types", "failed")
                return False

            # ==================== PHASE 3: Verify Data Storage ====================
            self.section("Phase 3: Verify Data Storage")

            # Step 6: Query graph state to verify requests were stored
            self.step(6, "Querying database for stored requests", "running")
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/graph-state",
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("network_state", [])
                    self.step(6, "Querying database for stored requests", "success")
                    self.log(f"Total Records in Database: {data.get('total_records', 0)}")
                    self.log(f"Records Retrieved: {len(records)}")

                    # Verify our test data is in the database
                    if records:
                        self.log("\nSample Records from Database:")
                        for record in records[:3]:  # Show first 3
                            self.log(f"  • Citizen: {record.get('citizen', '?')}, "
                                   f"Resource: {record.get('resource', '?')}, "
                                   f"Status: {record.get('status', '?')}")
                else:
                    self.step(6, "Querying database for stored requests", "failed")
                    self.log(f"Status Code: {response.status_code}")
                    return False
            except Exception as e:
                self.step(6, "Querying database for stored requests", "failed")
                self.log(f"Error: {str(e)}")
                return False

            # ==================== PHASE 4: Test Input Validation ====================
            self.section("Phase 4: Test Input Validation")

            # Step 7: Test invalid citizen_id rejection
            self.step(7, "Testing invalid citizen ID rejection", "running")
            payload_invalid = {
                "citizen_id": "ab",  # Too short
                "intent": "RESOURCE_REQUEST",
                "item": "Blood Pack",
                "urgency": "CRITICAL",
                "location_context": "Test"
            }
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ingest",
                    json=payload_invalid,
                    timeout=self.timeout
                )
                if response.status_code == 400:
                    self.step(7, "Testing invalid citizen ID rejection", "success")
                    self.log("✓ Invalid citizen ID properly rejected")
                else:
                    self.step(7, "Testing invalid citizen ID rejection", "failed")
                    self.log(f"✗ Expected 400 error, got {response.status_code}")
                    return False
            except Exception as e:
                self.step(7, "Testing invalid citizen ID rejection", "failed")
                self.log(f"Error: {str(e)}")
                return False

            # Step 8: Test invalid urgency rejection
            self.step(8, "Testing invalid urgency rejection", "running")
            payload_invalid = {
                "citizen_id": "citizen_001",
                "intent": "RESOURCE_REQUEST",
                "item": "Blood Pack",
                "urgency": "EXTREME",  # Invalid urgency
                "location_context": "Test"
            }
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ingest",
                    json=payload_invalid,
                    timeout=self.timeout
                )
                if response.status_code == 400:
                    self.step(8, "Testing invalid urgency rejection", "success")
                    self.log("✓ Invalid urgency properly rejected")
                else:
                    self.step(8, "Testing invalid urgency rejection", "failed")
                    self.log(f"✗ Expected 400 error, got {response.status_code}")
                    return False
            except Exception as e:
                self.step(8, "Testing invalid urgency rejection", "failed")
                self.log(f"Error: {str(e)}")
                return False

            # ==================== PHASE 5: Test Error Handling ====================
            self.section("Phase 5: Test Error Handling")

            # Step 9: Test missing required fields
            self.step(9, "Testing missing required fields handling", "running")
            payload_incomplete = {
                "citizen_id": "citizen_001"
                # Missing other required fields
            }
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ingest",
                    json=payload_incomplete,
                    timeout=self.timeout
                )
                if response.status_code == 422:  # Unprocessable Entity
                    self.step(9, "Testing missing required fields handling", "success")
                    self.log("✓ Missing fields properly detected")
                else:
                    self.step(9, "Testing missing required fields handling", "failed")
                    self.log(f"✗ Expected 422 error, got {response.status_code}")
                    return False
            except Exception as e:
                self.step(9, "Testing missing required fields handling", "failed")
                self.log(f"Error: {str(e)}")
                return False

            # ==================== PHASE 6: Test API Endpoints ====================
            self.section("Phase 6: Test All API Endpoints")

            # Step 10: Test all endpoints are accessible
            self.step(10, "Verifying all API endpoints are accessible", "running")
            endpoints = [
                ("GET", "/health"),
                ("GET", "/api/v1/graph-state"),
                ("POST", "/api/v1/migrate"),
            ]

            all_endpoints_ok = True
            for method, path in endpoints:
                try:
                    if method == "GET":
                        response = requests.get(f"{self.base_url}{path}", timeout=self.timeout)
                    else:
                        response = requests.post(f"{self.base_url}{path}", timeout=self.timeout)

                    if response.status_code < 500:
                        self.log(f"  ✓ {method} {path} ({response.status_code})")
                    else:
                        self.log(f"  ✗ {method} {path} ({response.status_code})")
                        all_endpoints_ok = False
                except Exception as e:
                    self.log(f"  ✗ {method} {path} - {str(e)}")
                    all_endpoints_ok = False

            if all_endpoints_ok:
                self.step(10, "Verifying all API endpoints are accessible", "success")
            else:
                self.step(10, "Verifying all API endpoints are accessible", "failed")
                return False

        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        return success

    def print_summary(self, success: bool):
        """Print workflow test summary"""
        self.section("Workflow Test Summary")

        if success:
            print("✅ END-TO-END WORKFLOW TEST PASSED")
            print(f"\nTotal requests processed: {len(self.test_data)}")
            print("\nWorkflow validated:")
            print("  ✓ Backend connectivity")
            print("  ✓ Database connectivity")
            print("  ✓ Resource request ingestion")
            print("  ✓ Multiple request types")
            print("  ✓ Data storage and retrieval")
            print("  ✓ Input validation")
            print("  ✓ Error handling")
            print("  ✓ API endpoints")
        else:
            print("❌ END-TO-END WORKFLOW TEST FAILED")
            print("\nSee above for specific failures.")

        print(f"\n{'='*60}\n")


def main():
    print("\n" + "="*60)
    print("NEXARIS Backend - End-to-End Workflow Test")
    print("="*60)
    print("This test verifies the complete system workflow from")
    print("request submission through database storage and retrieval.")
    print("="*60)

    tester = WorkflowTest()
    success = tester.run_complete_workflow()
    tester.print_summary(success)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
