#!/usr/bin/env python3
"""
Patient Tracker with Permission Fix
Automatically handles serial port permissions on Raspberry Pi
"""

import os
import sys
import subprocess
import serial
import time
import json
import sqlite3
import threading
import logging
from datetime import datetime
import pynmea2
import requests
from signal import signal, SIGINT
from sys import exit

def fix_serial_permissions():
    """Attempt to fix serial port permissions"""
    print("[PERMISSION] Checking serial port access...")
    
    # Check if we can access /dev/ttyS0
    try:
        with open('/dev/ttyS0', 'r') as f:
            pass
        print("✓ Can access /dev/ttyS0")
        return True
    except PermissionError:
        print("✗ Permission denied for /dev/ttyS0")
    
    # Try to fix permissions
    print("[PERMISSION] Attempting to fix...")
    
    # Method 1: Try to change permissions
    try:
        subprocess.run(['sudo', 'chmod', '666', '/dev/ttyS0'], check=True, capture_output=True)
        print("✓ Changed /dev/ttyS0 permissions")
        return True
    except:
        print("✗ Could not change permissions with chmod")
    
    # Method 2: Check if user is in dialout group
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        if 'dialout' in result.stdout:
            print("✓ User is in dialout group")
            return True
        else:
            print("✗ User not in dialout group")
            print("  Run: sudo usermod -a -G dialout $USER")
            print("  Then logout and login again")
    except:
        pass
    
    return False

class PatientTracker:
    def __init__(self):
        print("=" * 60)
        print("PATIENT TRACKING SYSTEM - RASPBERRY PI ZERO WH")
        print("=" * 60)
        
        # Try to fix permissions first
        if not fix_serial_permissions():
            print("\n" + "=" * 60)
            print("PERMISSION ERROR - SOLUTIONS:")
            print("=" * 60)
            print("1. QUICK FIX: Run with sudo:")
            print("   sudo python3 patient_tracker_fixed.py")
            print("")
            print("2. PROPER FIX: Add user to dialout group:")
            print("   sudo usermod -a -G dialout $USER")
            print("   logout && login")
            print("")
            print("3. TEMPORARY FIX: Run permission fix script:")
            print("   chmod +x fix_permissions.sh")
            print("   ./fix_permissions.sh")
            print("")
            print("4. CURRENT SESSION FIX:")
            print("   newgrp dialout")
            print("   python3 patient_tracker_fixed.py")
            print("=" * 60)
            sys.exit(1)
        
        # Hardcoded Raspberry Pi configuration
        self.patient_id = "PATIENT001"
        self.gps_port = "/dev/ttyS0"
        self.gps_baudrate = 9600
        self.gsm_port = "/dev/ttyUSB0"
        self.gsm_baudrate = 115200
        self.update_interval = 10
        self.emergency_numbers = ["+918848776875", "+9175929912412"]
        
        # Geofence configuration
        self.geofence_enabled = True
        self.geofence_lat = 40.7128
        self.geofence_lon = -74.0060
        self.geofence_radius = 100
        
        # Serial ports
        self.gps_serial = None
        self.gsm_serial = None
        
        # Database
        self.db_conn = None
        
        # Tracking state
        self.is_tracking = False
        self.current_location = None
        
        # Initialize components
        self.initialize_database()
        self.initialize_hardware()
        
        print(f"✓ Patient ID: {self.patient_id}")
        print(f"✓ GPS Port: {self.gps_port} @ {self.gps_baudrate} baud")
        print(f"✓ GSM Port: {self.gsm_port} @ {self.gsm_baudrate} baud")
        print(f"✓ Update Interval: {self.update_interval} seconds")
        print(f"✓ Geofence: {self.geofence_enabled} (radius: {self.geofence_radius}m)")
        
    def initialize_database(self):
        """Initialize SQLite database"""
        try:
            print("\n[DATABASE] Initializing...")
            self.db_conn = sqlite3.connect('patient_tracking.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    latitude REAL,
                    longitude REAL,
                    altitude REAL,
                    speed REAL,
                    timestamp DATETIME,
                    accuracy REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    alert_type TEXT,
                    message TEXT,
                    latitude REAL,
                    longitude REAL,
                    timestamp DATETIME,
                    resolved BOOLEAN DEFAULT 0
                )
            ''')
            
            self.db_conn.commit()
            print("✓ Database initialized successfully")
            
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise
    
    def initialize_hardware(self):
        """Initialize GPS and GSM hardware"""
        try:
            print("\n[GPS] Initializing GPS module...")
            self.gps_serial = serial.Serial(
                self.gps_port,
                self.gps_baudrate,
                timeout=1
            )
            print(f"✓ GPS connected on {self.gps_port}")
            
            print("\n[GSM] Initializing GSM module...")
            try:
                self.gsm_serial = serial.Serial(
                    self.gsm_port,
                    self.gsm_baudrate,
                    timeout=1
                )
                print(f"✓ GSM connected on {self.gsm_port}")
                self.test_gsm_module()
            except:
                print("⚠️  GSM module not found - continuing without SMS")
                self.gsm_serial = None
            
        except Exception as e:
            print(f"✗ Hardware initialization failed: {e}")
            print("  Make sure:")
            print("  - GPS is connected to GPIO 14/15 (ttyS0)")
            print("  - User has permission to access serial ports")
            raise
    
    def test_gsm_module(self):
        """Test GSM module connectivity"""
        if not self.gsm_serial:
            return
            
        try:
            print("\n[GSM] Testing module...")
            response = self.send_gsm_command('AT')
            if 'OK' in response:
                print("✓ GSM module responding")
            else:
                print("✗ GSM module not responding")
                return
            
            response = self.send_gsm_command('AT+CSQ')
            print(f"✓ Signal Strength: {response}")
            
            self.send_gsm_command('AT+CMGF=1')
            print("✓ SMS mode set to text")
            
        except Exception as e:
            print(f"✗ GSM test failed: {e}")
    
    def send_gsm_command(self, command, wait_time=1):
        """Send command to GSM module and return response"""
        if not self.gsm_serial:
            return ''
            
        try:
            self.gsm_serial.write((command + '\r\n').encode())
            time.sleep(wait_time)
            response = ''
            while self.gsm_serial.in_waiting > 0:
                response += self.gsm_serial.read(self.gsm_serial.in_waiting).decode()
            return response.strip()
        except Exception as e:
            print(f"GSM command failed: {command} - {e}")
            return ''
    
    def parse_gps_data(self, gps_data):
        """Parse NMEA GPS data"""
        try:
            for line in gps_data.split('\n'):
                if line.startswith('$GPGGA'):
                    msg = pynmea2.parse(line)
                    return {
                        'latitude': msg.latitude,
                        'longitude': msg.longitude,
                        'altitude': msg.altitude,
                        'timestamp': datetime.now(),
                        'fix_quality': msg.gps_qual,
                        'satellites': msg.num_sats
                    }
                elif line.startswith('$GPRMC'):
                    msg = pynmea2.parse(line)
                    return {
                        'latitude': msg.latitude,
                        'longitude': msg.longitude,
                        'speed': msg.spd_over_grnd,
                        'timestamp': datetime.now(),
                        'fix_valid': msg.is_valid
                    }
        except Exception as e:
            print(f"GPS parsing error: {e}")
        return None
    
    def get_gps_location(self):
        """Get current GPS location"""
        try:
            if self.gps_serial.in_waiting > 0:
                gps_data = self.gps_serial.read(self.gps_serial.in_waiting).decode()
                location = self.parse_gps_data(gps_data)
                if location:
                    self.current_location = location
                    return location
        except Exception as e:
            print(f"GPS reading error: {e}")
        return None
    
    def store_location(self, location):
        """Store location data in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO locations 
                (patient_id, latitude, longitude, altitude, speed, timestamp, accuracy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.patient_id,
                location.get('latitude'),
                location.get('longitude'),
                location.get('altitude'),
                location.get('speed'),
                location.get('timestamp'),
                location.get('accuracy', 10.0)
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"Database storage error: {e}")
    
    def check_geofence(self, location):
        """Check if patient is within geofence"""
        if not self.geofence_enabled:
            return True
        
        try:
            import math
            
            lat1 = math.radians(location['latitude'])
            lon1 = math.radians(location['longitude'])
            lat2 = math.radians(self.geofence_lat)
            lon2 = math.radians(self.geofence_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            r = 6371
            distance = c * r * 1000
            
            if distance > self.geofence_radius:
                self.trigger_alert('GEOFENCE_BREACH', 
                                 f"Patient left safe area. Distance: {distance:.2f}m",
                                 location['latitude'], location['longitude'])
                return False
            
            return True
            
        except Exception as e:
            print(f"Geofence check error: {e}")
            return True
    
    def trigger_alert(self, alert_type, message, latitude, longitude):
        """Trigger alert and send notifications"""
        try:
            print(f"\n🚨 ALERT: {alert_type}")
            print(f"   Message: {message}")
            print(f"   Location: {latitude:.6f}, {longitude:.6f}")
            print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO alerts 
                (patient_id, alert_type, message, latitude, longitude, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.patient_id, alert_type, message, latitude, longitude, datetime.now()))
            self.db_conn.commit()
            
            if self.gsm_serial:
                for number in self.emergency_numbers:
                    print(f"   Sending SMS to {number}...")
                    self.send_sms_alert(number, f"ALERT: {message}")
            else:
                print("   ⚠️  GSM not available - SMS not sent")
            
        except Exception as e:
            print(f"Alert triggering failed: {e}")
    
    def send_sms_alert(self, phone_number, message):
        """Send SMS alert via GSM module"""
        if not self.gsm_serial:
            return
            
        try:
            self.send_gsm_command(f'AT+CMGS="{phone_number}"', wait_time=2)
            self.gsm_serial.write((message + '\x1A').encode())
            time.sleep(2)
            response = self.send_gsm_command('', wait_time=2)
            print(f"   ✓ SMS sent to {phone_number}")
        except Exception as e:
            print(f"   ✗ SMS sending failed: {e}")
    
    def tracking_loop(self):
        """Main tracking loop with terminal output"""
        print(f"\n[TRACKING] Starting patient tracking...")
        print(f"   Update interval: {self.update_interval} seconds")
        print(f"   Press Ctrl+C to stop")
        print("-" * 60)
        
        loop_count = 0
        while self.is_tracking:
            try:
                loop_count += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Update #{loop_count}")
                
                location = self.get_gps_location()
                
                if location:
                    print(f"   📍 Location: {location['latitude']:.6f}, {location['longitude']:.6f}")
                    if location.get('altitude'):
                        print(f"   🏔️  Altitude: {location['altitude']:.1f}m")
                    if location.get('speed'):
                        print(f"   🚗 Speed: {location['speed']:.1f} knots")
                    if location.get('satellites'):
                        print(f"   🛰️  Satellites: {location['satellites']}")
                    
                    self.store_location(location)
                    print("   💾 Location saved to database")
                    
                    geofence_status = self.check_geofence(location)
                    if geofence_status:
                        print("   ✅ Within safe area")
                    
                else:
                    print("   ⚠️  No GPS data available")
                    print("   📡 Waiting for satellite lock...")
                
                print(f"   ⏳ Next update in {self.update_interval} seconds...")
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"   ✗ Tracking error: {e}")
                time.sleep(5)
    
    def start_tracking(self):
        """Start patient tracking"""
        if not self.is_tracking:
            self.is_tracking = True
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
    
    def stop_tracking(self):
        """Stop patient tracking"""
        self.is_tracking = False
        if hasattr(self, 'tracking_thread'):
            self.tracking_thread.join()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            print("\n[CLEANUP] Shutting down...")
            self.stop_tracking()
            if self.gps_serial:
                self.gps_serial.close()
                print("✓ GPS port closed")
            if self.gsm_serial:
                self.gsm_serial.close()
                print("✓ GSM port closed")
            if self.db_conn:
                self.db_conn.close()
                print("✓ Database closed")
            print("✓ Cleanup completed")
        except Exception as e:
            print(f"✗ Cleanup error: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n[SHUTDOWN] Received interrupt signal...')
    tracker.cleanup()
    exit(0)

if __name__ == "__main__":
    signal(SIGINT, signal_handler)
    
    try:
        tracker = PatientTracker()
        tracker.start_tracking()
        
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        if 'tracker' in locals():
            tracker.cleanup()
        exit(1)
