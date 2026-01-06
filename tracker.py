#!/usr/bin/env python3
"""
Patient Tracker - Run with: sudo python3 tracker.py
"""

import serial
import time
import sqlite3
import threading
from datetime import datetime
import math

print("=" * 50)
print("PATIENT TRACKER - RASPBERRY PI ZERO WH")
print("=" * 50)

# Configuration
PATIENT_ID = "PATIENT001"
GPS_PORT = "/dev/ttyS0"
GPS_BAUD = 9600
UPDATE_INTERVAL = 10

# Geofence (NYC coordinates)
SAFE_LAT = 40.7128
SAFE_LON = -74.0060
SAFE_RADIUS = 100  # meters

# Initialize
db = None
gps = None
running = False

def setup_db():
    """Setup database"""
    global db
    try:
        db = sqlite3.connect('patient.db')
        db.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY,
                patient TEXT,
                lat REAL,
                lon REAL,
                time DATETIME
            )
        ''')
        db.commit()
        print("✓ Database ready")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def setup_gps():
    """Setup GPS"""
    global gps
    try:
        print(f"Connecting GPS to {GPS_PORT}...")
        gps = serial.Serial(GPS_PORT, GPS_BAUD, timeout=2)
        print("✓ GPS connected")
        return True
    except Exception as e:
        print(f"✗ GPS error: {e}")
        print("\nFIX: Run with sudo")
        print("     sudo python3 tracker.py")
        return False

def parse_nmea(data):
    """Parse GPS data"""
    try:
        for line in data.split('\n'):
            if line.startswith('$GPGGA'):
                parts = line.split(',')
                if len(parts) > 5 and parts[2] and parts[4]:
                    lat = float(parts[2][:2]) + float(parts[2][2:]) / 60
                    if parts[3] == 'S': lat = -lat
                    lon = float(parts[4][:3]) + float(parts[4][3:]) / 60
                    if parts[5] == 'W': lon = -lon
                    return {'lat': lat, 'lon': lon, 'time': datetime.now()}
    except:
        pass
    return None

def get_location():
    """Get GPS location"""
    try:
        if gps.in_waiting > 0:
            data = gps.read(gps.in_waiting).decode()
            return parse_nmea(data)
    except:
        pass
    return None

def save_location(loc):
    """Save to database"""
    try:
        db.execute('''
            INSERT INTO locations (patient, lat, lon, time)
            VALUES (?, ?, ?, ?)
        ''', (PATIENT_ID, loc['lat'], loc['lon'], loc['time']))
        db.commit()
        print(f"✓ Saved: {loc['lat']:.6f}, {loc['lon']:.6f}")
    except Exception as e:
        print(f"Save error: {e}")

def check_geofence(loc):
    """Check if within safe area"""
    try:
        lat1 = math.radians(loc['lat'])
        lon1 = math.radians(loc['lon'])
        lat2 = math.radians(SAFE_LAT)
        lon2 = math.radians(SAFE_LON)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = c * 6371 * 1000  # meters
        
        if distance > SAFE_RADIUS:
            print(f"🚨 ALERT: Outside safe area! ({distance:.0f}m)")
        else:
            print(f"✅ Safe ({distance:.0f}m from center)")
    except:
        pass

def tracking_loop():
    """Main tracking loop"""
    global running
    count = 0
    
    print(f"\nTracking started (every {UPDATE_INTERVAL}s)")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    while running:
        try:
            count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] #{count}")
            
            loc = get_location()
            if loc:
                print(f"📍 {loc['lat']:.6f}, {loc['lon']:.6f}")
                save_location(loc)
                check_geofence(loc)
            else:
                print("⚠️  No GPS signal")
                print("📡 Waiting for satellites...")
            
            print(f"⏳ {UPDATE_INTERVAL}s...")
            time.sleep(UPDATE_INTERVAL)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

def cleanup():
    """Cleanup"""
    global running, gps, db
    running = False
    if gps:
        gps.close()
        print("✓ GPS closed")
    if db:
        db.close()
        print("✓ Database closed")

# Main execution
if __name__ == "__main__":
    try:
        if setup_db() and setup_gps():
            running = True
            tracking_loop()
        else:
            print("\nSetup failed. Check hardware connections.")
            print("GPS connections:")
            print("  VCC -> 3.3V")
            print("  GND -> GND")
            print("  TXD -> GPIO 15 (RXD)")
            print("  RXD -> GPIO 14 (TXD)")
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        cleanup()
        print("Goodbye!")
