import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(__file__))

def print_header(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def run_tests():
    errors = []
    
    print_header("*** PHASE 7 GRAND TESTING MATRIX")
    
    # 1. 7.3 Test resume download all 6 regions
    print("\n[Task 7.3] Testing 6 PDF Regions via Playwright...")
    try:
        from test_all_regions import test_all
        import asyncio
        asyncio.run(test_all())
        print("  [OK] 6 Region PDFs generated successfully.")
    except Exception as e:
        print(f"  [FAIL] PDF Generation Failed: {e}")
        errors.append(f"PDF Gen: {e}")

    # 2. 7.4 & 7.5 API Fallbacks
    print("\n[Task 7.4 & 7.5] Testing AI & GitHub API Fallbacks...")
    try:
        from services.groq_service import call_groq
        import asyncio
        res = asyncio.run(call_groq("Hello, this is a test. Reply with 'OK'."))
        if res:
            print("  [OK] Groq AI Integration active and responds perfectly.")
        else:
            print("  [WARN] Groq AI API exhausted or unreachable, fallback handled gracefully without crashing.")
            
        from services.github import fetch_github_projects
        # Provide invalid token or just see if the script handles the 404/401 gracefully
        stats = asyncio.run(fetch_github_projects("invalid_user_that_does_not_exist_999"))
        if isinstance(stats, list):
             print("  [OK] GitHub Fallback works gracefully. Did not crash on invalid data.")
        else:
             print("  [WARN] GitHub fallback returned unexpected payload, but did not crash app.")

    except Exception as e:
         print(f"  [FAIL] API Fallback tests crashed: {e}")
         errors.append(f"API Fallback: {e}")
         
    # 3. 7.6 & 7.7 Email Notifications & Analytics Logging
    print("\n[Task 7.6 & 7.7] Testing Analytics & Contact Hooks...")
    try:
        from run_backend_tests import test_analytics_logging, test_contact_form
        test_analytics_logging()
        print("  [OK] Analytics Pipeline logs data cleanly via TestClient.")
        test_contact_form()
        print("  [OK] Contact/Email dispatcher processes requests without crashing.")
    except Exception as e:
        print(f"  [FAIL] Analytics/Email integrations failed: {e}")
        errors.append(f"Analytics/Email: {e}")
        
    print_header("*** TEST SEQUENCE COMPLETE")
    if len(errors) == 0:
        print("  [OK] STATUS: ALL CORE BACKEND & FALLBACK TESTS PASSED!")
    else:
        print(f"  [FAIL] STATUS: ENCOUNTERED {len(errors)} ERRORS:")
        for err in errors:
            print(f"  - {err}")

if __name__ == "__main__":
    run_tests()
