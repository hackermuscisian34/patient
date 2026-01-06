#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

# Test the GPS fix
from patient_tracker import PatientTracker
import time

print("Testing GPS fix...")
print(f"OS: {os.name}")

# Create tracker instance
tracker = PatientTracker()
print(f"GPS Port in config: {tracker.config['gps_port']}")
print(f"GSM Port in config: {tracker.config['gsm_port']}")

# Test GPS location
print("\nTesting GPS location retrieval...")
location = tracker.get_gps_location()
if location:
    print(f"✓ GPS location acquired: {location['latitude']:.6f}, {location['longitude']:.6f}")
    print(f"  Altitude: {location.get('altitude', 'N/A')}")
    print(f"  Speed: {location.get('speed', 'N/A')}")
    print(f"  Timestamp: {location['timestamp']}")
else:
    print("✗ No GPS location available")

print("\nTest completed successfully!")
