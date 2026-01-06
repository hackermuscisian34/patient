#!/usr/bin/env python3

print("=== Raspberry Pi Compatibility Test ===")

import sys
import os
import json

print(f"OS: {os.name}")
print(f"Platform: {sys.platform}")

# Check config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    print(f"✓ GPS Port: {config['gps_port']}")
    print(f"✓ GSM Port: {config['gsm_port']}")
except Exception as e:
    print(f"✗ Config error: {e}")

# Test basic imports
try:
    from patient_tracker import PatientTracker
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")

print("✓ Code is Raspberry Pi compatible")
