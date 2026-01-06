#!/usr/bin/env python3
"""
Simple Patient Tracker for Raspberry Pi Zero WH
Run with: sudo python3 simple_tracker.py
"""

import serial
import time
import sqlite3
import threading
from datetime import datetime
import pynmea2
import math

class SimplePatientTracker:
    def __init__(self):
        print("=" * 50)
        print("SIMPLE PATIENT TRACKER")
        print("Raspberry Pi Zero WH")
        print("=" * 50)
        
        # Configuration
        self.patient_id = "PATIENT001"
        self.gps_port = "/dev/ttyS0"
        self.gps_baudrate = 9600
        self.update_interval = 10
        
        # Geofence
        self.geofence_lat = 40.7128
        self.geofence_lon = -74.0060
        self.geofence_radius = 100
        
        # Initialize
        self.db_conn = None
        self.gps_serial = None
        self.is_tracking = False
        
        # Setup
        self.setup_database()
        self.setup_gps()
        
    def setup_database(self):
        """Setup SQLite database"""
        try:
            self.db_conn = sqlite3.connect('patient_tracking.db')
            cursor = self.db_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY,
                    patient_id TEXT,
                    latitude REAL,
                    longitude REAL,
                    timestamp DATETIME
                )
            ''')
            self.db_conn.commit()
            print("✓ Database ready")
        except Exception as e:
            print(f"✗ Database error: {e}")
            
    def setup_gps(self):
        """Setup GPS module"""
        try:
            print(f"Connecting to GPS on {self.gps_port}...")
            self.gps_serial = serial.Serial(self.gps_port, self.gps_baudrate, timeout=2)
            print("✓ GPS connected")
        except Exception as e:
            print(f"✗ GPS error: {e}")
            print("\nSOLUTIONS:")
            print("1. Run with sudo: sudo python3 simple_tracker.py")
            print("2. Add user to dialout group: sudo usermod -a -G dialout $USER")
            print("3. Logout and login again")
            exit(1)
    
    def parse_gps(self, data):
        """Parse GPS data"""
        try:
            for line in data.split('\n'):
                if line.startswith('$GPGGA'):
                    msg = pynmea2.parse(line)
                    return {
                        'lat': msg.latitude,
                        'lon': msg.longitude,
                        'time': datetime.now()
                    }
        except:
            pass
        return None
    
    def get_location(self):
        """Get GPS location"""
        try:
            if self.gps_serial.in_waiting > 0:
                data = self.gps_serial.read(self.gps_serial.in_waiting).decode()
                return self.parse_gps(data)
        except Exception as e:
            print(f"GPS read error: {e}")
        return None
    
    def save_location(self, location):
        """Save location to database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO locations (patient_id, latitude, longitude, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (self.patient_id, location['lat'], location['lon'], location['time']))
            self.db_conn.commit()
            print(f"✓ Saved: {location['lat']:.6f}, {location['lon']:.6f}")
        except Exception as e:
            print(f"Save error: {e}")
    
    def check_geofence(self, location):
        """Check if within geofence"""
        try:
            lat1 = math.radians(location['lat'])
            lon1 = math.radians(location['lon'])
            lat2 = math.radians(self.geofence_lat)
            lon2 = math.radians(self.geofence_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = c * 6371 * 1000  # meters
            
            if distance > self.geofence_radius:
                print(f"🚨 ALERT: Outside safe area! ({distance:.0f}m)")
            else:
                print(f"✅ Within safe area ({distance:.0f}m)")
        except Exception as e:
            print(f"Geofence error: {e}")
    
    def track_loop(self):
        """Main tracking loop"""
        print(f"\nStarting tracking (every {self.update_interval}s)...")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        count = 0
        while self.is_tracking:
            try:
                count += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Update #{count}")
                
                location = self.get_location()
                if location:
                    print(f"📍 Location: {location['lat']:.6f}, {location['lon']:.6f}")
                    self.save_location(location)
                    self.check_geofence(location)
                else:
                    print("⚠️  No GPS signal")
                    print("📡 Waiting for satellites...")
                
                print(f"⏳ Next update in {self.update_interval}s...")
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start tracking"""
        self.is_tracking = True
        self.track_thread = threading.Thread(target=self.track_loop)
        self.track_thread.daemon = True
        self.track_thread.start()
    
    def stop(self):
        """Stop tracking"""
        self.is_tracking = False
        if hasattr(self, 'track_thread'):
            self.track_thread.join()
        if self.gps_serial:
            self.gps_serial.close()
        if self.db_conn:
            self.db_conn.close()
        print("\n✓ Stopped")

if __name__ == "__main__":
    try:
        tracker = SimplePatientTracker()
        tracker.start()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        tracker.stop()
        print("Goodbye!")
    except Exception as e:
        print(f"\nFatal error: {e}")
        if 'tracker' in locals():
            tracker.stop()
