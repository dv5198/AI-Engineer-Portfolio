import sys
import os

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

from main import app

print("Registered Routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"[{getattr(route, 'methods', 'GET')}] {route.path}")
    else:
        print(f"[UNKNOWN] {route}")
