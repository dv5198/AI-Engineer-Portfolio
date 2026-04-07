from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    print("Testing /api/admin/rewrite-about/ ...")
    res1 = client.post("/api/admin/rewrite-about/", json={"text": "I like coding", "instruction": "Make it pro"})
    print("Status:", res1.status_code)
    print("Response:", res1.json())
    
    print("\nTesting /api/admin/test-grok/ ...")
    res2 = client.post("/api/admin/test-grok/", json={"message": "Hey"})
    print("Status:", res2.status_code)
    print("Response:", res2.json())
    
    print("\nTesting /api/admin/rewrite-summary/ ...")
    res3 = client.post("/api/admin/rewrite-summary/", json={"about_list": ["I am a dev", "I use python"]})
    print("Status:", res3.status_code)
    print("Response:", res3.json())
    
    print("\nTesting /api/admin/generate-bullets/ ...")
    res4 = client.post("/api/admin/generate-bullets/", json={
        "role": "Software Engineer", 
        "company": "Tech Corp", 
        "description": "I did backend stuff."
    })
    print("Status:", res4.status_code)
    print("Response:", res4.json())
    
    print("\nTesting /api/resume/download (Auto) ...")
    res5 = client.get("/api/resume/download")
    print("Status:", res5.status_code)
    print("Content-Type:", res5.headers.get("Content-Type"))

if __name__ == "__main__":
    run_tests()
