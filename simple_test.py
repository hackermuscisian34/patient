import os
print(f"OS: {os.name}")
import sys
sys.path.insert(0, '.')
from patient_tracker import PatientTracker
t = PatientTracker()
print(f"GPS Port: {t.config['gps_port']}")
loc = t.get_gps_location()
print(f"Location available: {loc is not None}")
if loc:
    print(f"Lat: {loc['latitude']}, Lon: {loc['longitude']}")
