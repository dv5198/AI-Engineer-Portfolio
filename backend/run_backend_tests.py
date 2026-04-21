import sys
from fastapi.testclient import TestClient
from main import app
import json
import logging

# Suppress noisy logs for cleaner output
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)

client = TestClient(app)

errors = []

def run_test(name, callback):
    print(f"Running test: {name} ... ", end="")
    try:
        callback()
        print("[PASS]")
    except Exception as e:
        print("[FAIL]")
        errors.append(f"[{name}] {str(e)}")

def test_portfolio_get():
    res = client.get("/api/portfolio/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    # Verify default str is accessible
    data = res.json()
    assert "profile" in data, "Missing profile key"

def test_portfolio_post_no_background_failure():
    payload = {
        "profile": {
            "name": "Divya Nirankari"
        }
    }
    # This should trigger our new active Task 4.22 via background tasks
    res = client.post("/api/portfolio/", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Response: {res.text}"

def test_admin_login_auth():
    # Provide the default correct password to test auth logic
    res = client.post("/api/admin/login/", json={"password": "admin123"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "token" in res.json()

def test_crud_dynamic_sections():
    # Test creation
    item = {
        "topic": "Quantum Machine Learning",
        "description": "Investigating QAI",
        "order": 1,
        "visible": True
    }
    res = client.post("/api/dynamic/researchInterests", json=item)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Details: {res.text}"
    created_id = res.json().get("id")

    # Test toggle visibility
    res = client.patch(f"/api/dynamic/researchInterests/{created_id}/visibility")
    assert res.status_code == 200, f"Toggle visibility failed: {res.status_code} - {res.text}"

def test_contact_form():
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Phase 7 Check",
        "message": "Hello world"
    }
    res = client.post("/api/platform/contact/send/", json=payload)
    assert res.status_code == 200, f"Contact form failed: {res.text}"

def test_analytics_logging():
    payload = {
        "event": "page_view",
        "details": "hero",
        "timestamp": 1600000000
    }
    res = client.post("/api/platform/event/", json=payload)
    assert res.status_code == 200, f"Event log failed: {res.text}"
    
    res2 = client.get("/api/platform/summary/")
    assert res2.status_code == 200, f"Summary get failed: {res2.text}"

def test_resume_download_background():
    # Mocking request to test 4.20 logic
    res = client.get("/api/resume/download")
    assert res.status_code == 200, f"Resume download failed: {res.text}"
    assert res.headers["content-type"] == "application/pdf", "Did not return PDF"

# Run tests
run_test("GET /api/portfolio/", test_portfolio_get)
run_test("POST /api/portfolio/ (Triggers task 4.21 & 4.22)", test_portfolio_post_no_background_failure)
run_test("POST /api/admin/login/", test_admin_login_auth)
run_test("CRUD Factory Operations (Dynamic Sections)", test_crud_dynamic_sections)
run_test("POST /api/platform/contact/send/ (Task 4.16 SMTP)", test_contact_form)
run_test("Analytics pipeline (Tasks 4.17 & 4.18)", test_analytics_logging)
run_test("GET /api/resume/download (Task 4.20 PDF+Email)", test_resume_download_background)

print("\n--- TEST SUMMARY ---")
if len(errors) == 0:
    print("ALL TESTS PASSED SUCCESSFULLY! No bugs detected in Phase 4 routing logic.")
else:
    print(f"Encountered {len(errors)} issues:")
    for err in errors:
        print(err)
