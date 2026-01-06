import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Python path:", sys.path)
print("Current directory:", os.getcwd())
print("Script directory:", os.path.dirname(os.path.abspath(__file__)))

try:
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    print("✓ Config loaded:", config)
except Exception as e:
    print("✗ Config error:", e)

try:
    import sqlite3
    conn = sqlite3.connect('patient_tracking.db')
    print("✓ Database connection successful")
    conn.close()
except Exception as e:
    print("✗ Database error:", e)

try:
    import serial
    print("✓ Serial module available")
except Exception as e:
    print("✗ Serial error:", e)

print("\nTesting patient_tracker import...")
try:
    from patient_tracker import PatientTracker
    print("✓ PatientTracker imported successfully")
except Exception as e:
    print("✗ PatientTracker import error:", e)

print("\nTesting Windows version import...")
try:
    from patient_tracker_windows import PatientTrackerWindows
    print("✓ PatientTrackerWindows imported successfully")
except Exception as e:
    print("✗ PatientTrackerWindows import error:", e)

input("\nPress Enter to continue...")
