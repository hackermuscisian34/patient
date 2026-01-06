#!/usr/bin/env python3
"""
Patient Tracking System - Raspberry Pi Zero WH
Complete GPS + GSM + Geofence + SMS Alert System
"""

import serial
import time
import sqlite3
import threading
import math
from datetime import datetime
import pynmea2
from signal import signal, SIGINT
from sys import exit

class PatientTracker:
    def __init__(self):
        print("=" * 60)
        print("PATIENT TRACKING SYSTEM")
        print("Raspberry Pi Zero WH")
        print("=" * 60)
        
        # Patient Configuration
        self.patient_id = "PATIENT001"
        self.emergency_contacts = ["+918848776875", "+9175929912412"]
        
        # Hardware Configuration
        self.gps_port = "/dev/ttyS0"
        self.gps_baudrate = 9600
        self.gsm_port = "/dev/ttyUSB0"
        self.gsm_baudrate = 115200
        
        # Tracking Configuration
        self.update_interval = 10  # seconds
        self.geofence_enabled = True
        self.geofence_lat = 40.7128  # Default: NYC
        self.geofence_lon = -74.0060
        self.geofence_radius = 100  # meters
        
        # System State
        self.gps_serial = None
        self.gsm_serial = None
        self.db_conn = None
        self.is_tracking = False
        self.current_location = None
        
        # Initialize System
        self.initialize_database()
        self.initialize_hardware()
        self.display_configuration()
        
    def display_configuration(self):
        """Display current configuration"""
        print(f"\n📋 CONFIGURATION:")
        print(f"   Patient ID: {self.patient_id}")
        print(f"   GPS Port: {self.gps_port} @ {self.gps_baudrate} baud")
        print(f"   GSM Port: {self.gsm_port} @ {self.gsm_baudrate} baud")
        print(f"   Update Interval: {self.update_interval} seconds")
        print(f"   Geofence: {'ENABLED' if self.geofence_enabled else 'DISABLED'}")
        if self.geofence_enabled:
            print(f"   Safe Area: {self.geofence_lat:.4f}, {self.geofence_lon:.4f}")
            print(f"   Safe Radius: {self.geofence_radius} meters")
        print(f"   Emergency Contacts: {len(self.emergency_contacts)} numbers")
        
    def initialize_database(self):
        """Initialize SQLite database"""
        try:
            print("\n🗄️  Initializing database...")
            self.db_conn = sqlite3.connect('patient_tracking.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            # Locations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    latitude REAL,
                    longitude REAL,
                    altitude REAL,
                    speed REAL,
                    timestamp DATETIME,
                    satellites INTEGER,
                    accuracy REAL
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    alert_type TEXT,
                    message TEXT,
                    latitude REAL,
                    longitude REAL,
                    timestamp DATETIME,
                    sms_sent BOOLEAN DEFAULT 0,
                    resolved BOOLEAN DEFAULT 0
                )
            ''')
            
            # System status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT,
                    status TEXT,
                    message TEXT,
                    timestamp DATETIME
                )
            ''')
            
            self.db_conn.commit()
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise
    
    def initialize_hardware(self):
        """Initialize GPS and GSM hardware"""
        try:
            # Initialize GPS
            print(f"\n🛰️  Initializing GPS module...")
            self.gps_serial = serial.Serial(
                self.gps_port,
                self.gps_baudrate,
                timeout=2
            )
            print(f"✅ GPS connected on {self.gps_port}")
            
            # Initialize GSM (optional)
            print(f"\n📱 Initializing GSM module...")
            try:
                self.gsm_serial = serial.Serial(
                    self.gsm_port,
                    self.gsm_baudrate,
                    timeout=2
                )
                print(f"✅ GSM connected on {self.gsm_port}")
                self.test_gsm_module()
            except Exception as e:
                print(f"⚠️  GSM module not available: {e}")
                print("   System will continue without SMS alerts")
                self.gsm_serial = None
            
            self.log_system_status("HARDWARE", "INITIALIZED", "GPS and GSM modules initialized")
            
        except Exception as e:
            print(f"❌ Hardware initialization failed: {e}")
            print("\n🔧 HARDWARE TROUBLESHOOTING:")
            print("   GPS Connections:")
            print("     VCC -> 3.3V or 5V")
            print("     GND -> GND")
            print("     TXD -> GPIO 15 (RXD)")
            print("     RXD -> GPIO 14 (TXD)")
            print("   GSM Connections:")
            print("     USB -> Raspberry Pi USB port")
            print("     SIM card inserted")
            print("   Permission Fix:")
            print("     sudo usermod -a -G dialout $USER")
            print("     logout && login")
            print("   Or run with: sudo python3 patient_tracker.py")
            raise
    
    def test_gsm_module(self):
        """Test GSM module functionality"""
        if not self.gsm_serial:
            return
            
        try:
            print("   Testing GSM module...")
            
            # Basic AT command
            response = self.send_gsm_command('AT')
            if 'OK' in response:
                print("   ✅ GSM module responding")
            else:
                print("   ⚠️  GSM module not responding properly")
                return
            
            # Get module info
            response = self.send_gsm_command('ATI')
            if response:
                print(f"   📱 Module: {response}")
            
            # Check signal strength
            response = self.send_gsm_command('AT+CSQ')
            if response:
                print(f"   📶 Signal: {response}")
            
            # Set SMS mode
            self.send_gsm_command('AT+CMGF=1')
            print("   ✅ SMS mode configured")
            
        except Exception as e:
            print(f"   ⚠️  GSM test failed: {e}")
    
    def send_gsm_command(self, command, wait_time=1):
        """Send AT command to GSM module"""
        if not self.gsm_serial:
            return ""
            
        try:
            self.gsm_serial.write((command + '\r\n').encode())
            time.sleep(wait_time)
            response = ''
            while self.gsm_serial.in_waiting > 0:
                response += self.gsm_serial.read(self.gsm_serial.in_waiting).decode()
            return response.strip()
        except Exception as e:
            return ""
    
    def parse_gps_data(self, raw_data):
        """Parse NMEA GPS data"""
        try:
            for line in raw_data.split('\n'):
                line = line.strip()
                if not line or not line.startswith('$'):
                    continue
                    
                try:
                    if line.startswith('$GPGGA'):
                        msg = pynmea2.parse(line)
                        return {
                            'latitude': msg.latitude,
                            'longitude': msg.longitude,
                            'altitude': msg.altitude,
                            'timestamp': datetime.now(),
                            'satellites': msg.num_sats,
                            'fix_quality': msg.gps_qual,
                            'hdop': getattr(msg, 'hdop', None)
                        }
                    elif line.startswith('$GPRMC'):
                        msg = pynmea2.parse(line)
                        return {
                            'latitude': msg.latitude,
                            'longitude': msg.longitude,
                            'speed': msg.spd_over_grnd * 1.852 if msg.spd_over_grnd else 0,  # Convert knots to km/h
                            'timestamp': datetime.now(),
                            'fix_valid': msg.is_valid
                        }
                except pynmea2.ParseError:
                    continue
                    
        except Exception as e:
            print(f"   GPS parsing error: {e}")
        
        return None
    
    def get_gps_location(self):
        """Get current GPS location"""
        try:
            if self.gps_serial and self.gps_serial.in_waiting > 0:
                raw_data = self.gps_serial.read(self.gps_serial.in_waiting).decode('ascii', errors='ignore')
                location = self.parse_gps_data(raw_data)
                if location:
                    self.current_location = location
                    return location
        except Exception as e:
            print(f"   GPS reading error: {e}")
        
        return None
    
    def store_location(self, location):
        """Store location data in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO locations 
                (patient_id, latitude, longitude, altitude, speed, timestamp, satellites, accuracy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.patient_id,
                location.get('latitude'),
                location.get('longitude'),
                location.get('altitude'),
                location.get('speed'),
                location.get('timestamp'),
                location.get('satellites'),
                location.get('hdop')
            ))
            self.db_conn.commit()
            
        except Exception as e:
            print(f"   Database storage error: {e}")
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula"""
        try:
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in meters
            distance = c * 6371000
            return distance
            
        except Exception as e:
            print(f"   Distance calculation error: {e}")
            return float('inf')
    
    def check_geofence(self, location):
        """Check if patient is within geofence"""
        if not self.geofence_enabled:
            return True
        
        try:
            distance = self.calculate_distance(
                location['latitude'],
                location['longitude'],
                self.geofence_lat,
                self.geofence_lon
            )
            
            if distance > self.geofence_radius:
                self.trigger_alert(
                    'GEOFENCE_BREACH',
                    f"Patient left safe area. Distance: {distance:.1f}m from center",
                    location['latitude'],
                    location['longitude']
                )
                return False
            else:
                return True
                
        except Exception as e:
            print(f"   Geofence check error: {e}")
            return True
    
    def trigger_alert(self, alert_type, message, latitude, longitude):
        """Trigger alert and send notifications"""
        try:
            print(f"\n🚨 ALERT: {alert_type}")
            print(f"   📝 Message: {message}")
            print(f"   📍 Location: {latitude:.6f}, {longitude:.6f}")
            print(f"   ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Store alert in database
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO alerts 
                (patient_id, alert_type, message, latitude, longitude, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.patient_id, alert_type, message, latitude, longitude, datetime.now()))
            self.db_conn.commit()
            
            # Send SMS alerts
            sms_sent_count = 0
            if self.gsm_serial:
                for number in self.emergency_contacts:
                    print(f"   📱 Sending SMS to {number}...")
                    if self.send_sms_alert(number, f"ALERT: {message}"):
                        sms_sent_count += 1
                        print(f"   ✅ SMS sent to {number}")
                    else:
                        print(f"   ❌ SMS failed to {number}")
            else:
                print("   ⚠️  GSM not available - SMS alerts disabled")
            
            # Update alert record
            cursor.execute('''
                UPDATE alerts SET sms_sent = ? WHERE id = last_insert_rowid()
            ''', (sms_sent_count > 0,))
            self.db_conn.commit()
            
            self.log_system_status("ALERT", alert_type, message)
            
        except Exception as e:
            print(f"   Alert triggering failed: {e}")
    
    def send_sms_alert(self, phone_number, message):
        """Send SMS alert via GSM module"""
        if not self.gsm_serial:
            return False
            
        try:
            # Send SMS command
            self.gsm_serial.write(f'AT+CMGS="{phone_number}"\r\n'.encode())
            time.sleep(1)
            
            # Send message content
            self.gsm_serial.write(f'{message}\x1A'.encode())
            time.sleep(2)
            
            # Check response
            response = ''
            while self.gsm_serial.in_waiting > 0:
                response += self.gsm_serial.read(self.gsm_serial.in_waiting).decode()
            
            return '+CMGS:' in response
            
        except Exception as e:
            print(f"   SMS sending error: {e}")
            return False
    
    def log_system_status(self, component, status, message):
        """Log system status to database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO system_status (component, status, message, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (component, status, message, datetime.now()))
            self.db_conn.commit()
        except Exception as e:
            pass  # Silent fail for logging
    
    def tracking_loop(self):
        """Main tracking loop"""
        print(f"\n🚀 Starting patient tracking...")
        print(f"   Update interval: {self.update_interval} seconds")
        print(f"   Press Ctrl+C to stop")
        print("-" * 60)
        
        update_count = 0
        consecutive_failures = 0
        
        while self.is_tracking:
            try:
                update_count += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Update #{update_count}")
                
                # Get GPS location
                location = self.get_gps_location()
                
                if location:
                    consecutive_failures = 0
                    
                    # Display location info
                    print(f"   📍 Location: {location['latitude']:.6f}, {location['longitude']:.6f}")
                    if location.get('altitude'):
                        print(f"   🏔️  Altitude: {location['altitude']:.1f}m")
                    if location.get('speed'):
                        print(f"   🚗 Speed: {location['speed']:.1f} km/h")
                    if location.get('satellites'):
                        print(f"   🛰️  Satellites: {location['satellites']}")
                    if location.get('fix_quality'):
                        fix_status = "Good" if location['fix_quality'] >= 1 else "Poor"
                        print(f"   📡 GPS Fix: {fix_status}")
                    
                    # Store location
                    self.store_location(location)
                    print("   💾 Location saved to database")
                    
                    # Check geofence
                    if self.geofence_enabled:
                        geofence_status = self.check_geofence(location)
                        if geofence_status:
                            distance = self.calculate_distance(
                                location['latitude'], location['longitude'],
                                self.geofence_lat, self.geofence_lon
                            )
                            print(f"   ✅ Within safe area ({distance:.0f}m from center)")
                    
                else:
                    consecutive_failures += 1
                    print(f"   ⚠️  No GPS data available")
                    print(f"   📡 Waiting for satellite lock... (attempt {consecutive_failures})")
                    
                    if consecutive_failures >= 6:  # 1 minute of failures
                        print(f"   🚨 GPS signal lost for {consecutive_failures * self.update_interval} seconds")
                        self.trigger_alert(
                            'GPS_LOST',
                            f"GPS signal lost for {consecutive_failures * self.update_interval} seconds",
                            self.current_location['latitude'] if self.current_location else 0,
                            self.current_location['longitude'] if self.current_location else 0
                        )
                
                # Wait for next update
                print(f"   ⏳ Next update in {self.update_interval} seconds...")
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"   ❌ Tracking error: {e}")
                time.sleep(5)
    
    def start_tracking(self):
        """Start patient tracking"""
        if not self.is_tracking:
            self.is_tracking = True
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
            self.log_system_status("TRACKING", "STARTED", "Patient tracking started")
    
    def stop_tracking(self):
        """Stop patient tracking"""
        self.is_tracking = False
        if hasattr(self, 'tracking_thread'):
            self.tracking_thread.join(timeout=5)
        self.log_system_status("TRACKING", "STOPPED", "Patient tracking stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            print("\n🧹 Shutting down system...")
            
            self.stop_tracking()
            
            if self.gps_serial:
                self.gps_serial.close()
                print("✅ GPS port closed")
            
            if self.gsm_serial:
                self.gsm_serial.close()
                print("✅ GSM port closed")
            
            if self.db_conn:
                self.db_conn.close()
                print("✅ Database closed")
            
            print("✅ System shutdown complete")
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n🛑 Received interrupt signal...')
    if 'tracker' in globals():
        tracker.cleanup()
    exit(0)

if __name__ == "__main__":
    # Setup signal handler for graceful shutdown
    signal(SIGINT, signal_handler)
    
    try:
        # Create and start patient tracker
        tracker = PatientTracker()
        tracker.start_tracking()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        if 'tracker' in globals():
            tracker.cleanup()
        exit(1)
