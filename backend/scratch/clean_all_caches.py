import os
import shutil
import sqlite3

BASE_DIR = "d:/project/backend"
GENERATED_DIR = os.path.join(BASE_DIR, "generated_pdfs")
TEST_OUTPUTS_DIR = os.path.join(BASE_DIR, "test_outputs")
DB_FILE = os.path.join(BASE_DIR, "portfolio.db")

def clean_all_caches():
    print("--- STARTING CACHE AND PREGENERATED FILES CLEANUP ---")
    
    # 1. Clear generated_pdfs directory
    if os.path.exists(GENERATED_DIR):
        print(f"Deleting pregenerated PDFs folder: {GENERATED_DIR}")
        try:
            shutil.rmtree(GENERATED_DIR)
        except Exception as e:
            print(f"Error deleting pregenerated PDFs folder: {e}")
    os.makedirs(GENERATED_DIR, exist_ok=True)
    print("OK: Pregenerated PDFs folder cleared.")
    
    # 2. Clear test_outputs directory
    if os.path.exists(TEST_OUTPUTS_DIR):
        print(f"Deleting test outputs folder: {TEST_OUTPUTS_DIR}")
        try:
            shutil.rmtree(TEST_OUTPUTS_DIR)
        except Exception as e:
            print(f"Error deleting test outputs folder: {e}")
    os.makedirs(TEST_OUTPUTS_DIR, exist_ok=True)
    print("OK: Test outputs folder cleared.")

    # 3. Clear SQLite pdf_cache table
    if os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pdf_cache")
            print(f"OK: Cleared {cursor.rowcount} entries from SQLite pdf_cache table.")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error clearing SQLite cache: {e}")
            
    print("--- CLEANUP COMPLETE ---")

if __name__ == "__main__":
    clean_all_caches()
