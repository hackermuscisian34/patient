#!/usr/bin/env python3
"""
Patient Tracking System - Windows Test Version
Simulates GPS and GSM modules for testing without hardware
"""

import time
import json
import sqlite3
import threading
import logging
from datetime import datetime
import random
import math

class MockSerial:
    """Mock serial port for testing"""
    def __init__(self, port, baudrate, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.in_waiting = 0
        self.buffer = ""
        
    def write(self, data):
        pass
        
    def read(self, size):
        # Simulate GPS NMEA data
        if "COM1" in self.port:  # GPS
            nmea = f"$GPGGA,{datetime.now().strftime('%H%M%S')},{40.7128 + random.uniform(-0.001, 0.001):.4f},{'N'},{-74.0060 + random.uniform(-0.001, 0.001):.4f},{'W'},1,08,0.9,10.0,M,46.9,M,,*47\r\n"
            return nmea.encode()
        return b""
        
    def close(self):
        pass

class PatientTrackerWindows:
    def __init__(self):
        # Configuration
        self.config = self.load_config()
        
        # Serial ports (mocked for Windows)
        self.gps_port = None
        self.gsm_port = None
        
        # Database
        self.db_conn = None
        
        # Tracking state
        self.is_tracking = False
        self.current_location = None
        self.patient_id = self.config.get('patient_id', 'PATIENT001')
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.initialize_database()
        self.initialize_serial_ports()
        
    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration for Windows
            default_config = {
                "patient_id": "PATIENT001",
                "gps_port": "COM1",
                "gps_baudrate": 9600,
                "gsm_port": "COM2",
                "gsm_baudrate": 115200,
                "server_url": "",
                "update_interval": 5,
                "emergency_numbers": ["+918848776875", "+9175929912412"],
                "geofence": {
                    "enabled": True,
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "radius": 100
                }
            }
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('patient_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_database(self):
        """Initialize SQLite database for storing location data"""
        try:
            self.db_conn = sqlite3.connect('patient_tracking.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            # Create tables
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
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def initialize_serial_ports(self):
        """Initialize GPS and GSM serial connections (mocked for Windows)"""
        try:
            # Initialize GPS (mock)
            self.gps_port = MockSerial(
                self.config['gps_port'],
                self.config['gps_baudrate'],
                timeout=1
            )
            self.logger.info(f"GPS simulated on {self.config['gps_port']}")
            
            # Initialize GSM (mock)
            self.gsm_port = MockSerial(
                self.config['gsm_port'],
                self.config['gsm_baudrate'],
                timeout=1
            )
            self.logger.info(f"GSM simulated on {self.config['gsm_port']}")
            
            # Test GSM module (mock)
            self.test_gsm_module()
            
        except Exception as e:
            self.logger.error(f"Serial port initialization failed: {e}")
            raise
    
    def test_gsm_module(self):
        """Test GSM module connectivity (mock)"""
        try:
            self.logger.info("GSM Module: SIM800L Mock")
            self.logger.info("Signal Strength: Mock Signal")
            self.logger.info("SMS mode: Text mode enabled")
            
        except Exception as e:
            self.logger.error(f"GSM module test failed: {e}")
            raise
    
    def parse_gps_data(self, gps_data):
        """Parse NMEA GPS data (simplified)"""
        try:
            # Simple parsing for demo
            if "$GPGGA" in gps_data:
                # Generate mock location data
                return {
                    'latitude': 40.7128 + random.uniform(-0.01, 0.01),
                    'longitude': -74.0060 + random.uniform(-0.01, 0.01),
                    'altitude': 10.0 + random.uniform(-5, 5),
                    'timestamp': datetime.now(),
                    'fix_quality': 1,
                    'satellites': 8
                }
        except Exception as e:
            self.logger.error(f"GPS parsing error: {e}")
        return None
    
    def get_gps_location(self):
        """Get current GPS location"""
        try:
            # Simulate GPS data availability
            gps_data = self.gps_port.read(100).decode()
            location = self.parse_gps_data(gps_data)
            if location:
                self.current_location = location
                return location
        except Exception as e:
            self.logger.error(f"GPS reading error: {e}")
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
                location.get('speed', 0.0),
                location.get('timestamp'),
                location.get('accuracy', 10.0)
            ))
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"Database storage error: {e}")
    
    def check_geofence(self, location):
        """Check if patient is within geofence"""
        if not self.config['geofence']['enabled']:
            return True
        
        try:
            lat1 = math.radians(location['latitude'])
            lon1 = math.radians(location['longitude'])
            lat2 = math.radians(self.config['geofence']['latitude'])
            lon2 = math.radians(self.config['geofence']['longitude'])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            r = 6371  # Earth's radius in km
            distance = c * r * 1000  # Convert to meters
            
            if distance > self.config['geofence']['radius']:
                self.trigger_alert('GEOFENCE_BREACH', 
                                 f"Patient left safe area. Distance: {distance:.2f}m",
                                 location['latitude'], location['longitude'])
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Geofence check error: {e}")
            return True
    
    def trigger_alert(self, alert_type, message, latitude, longitude):
        """Trigger alert and send notifications (mock)"""
        try:
            # Store alert in database
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO alerts 
                (patient_id, alert_type, message, latitude, longitude, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.patient_id, alert_type, message, latitude, longitude, datetime.now()))
            self.db_conn.commit()
            
            # Mock SMS alerts
            for number in self.config['emergency_numbers']:
                self.logger.info(f"MOCK SMS to {number}: ALERT: {message}")
            
            self.logger.warning(f"Alert triggered: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Alert triggering failed: {e}")
    
    def tracking_loop(self):
        """Main tracking loop"""
        self.logger.info("Starting patient tracking...")
        
        while self.is_tracking:
            try:
                # Get GPS location
                location = self.get_gps_location()
                
                if location:
                    # Store location
                    self.store_location(location)
                    
                    # Check geofence
                    self.check_geofence(location)
                    
                    self.logger.info(f"Location updated: {location['latitude']:.6f}, {location['longitude']:.6f}")
                else:
                    self.logger.warning("No GPS data available")
                
                # Wait for next update
                time.sleep(self.config['update_interval'])
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Tracking loop error: {e}")
                time.sleep(5)
    
    def start_tracking(self):
        """Start patient tracking"""
        if not self.is_tracking:
            self.is_tracking = True
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
            self.logger.info("Patient tracking started")
    
    def stop_tracking(self):
        """Stop patient tracking"""
        self.is_tracking = False
        if hasattr(self, 'tracking_thread'):
            self.tracking_thread.join()
        self.logger.info("Patient tracking stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_tracking()
            if self.gps_port:
                self.gps_port.close()
            if self.gsm_port:
                self.gsm_port.close()
            if self.db_conn:
                self.db_conn.close()
            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

if __name__ == "__main__":
    try:
        # Create and start tracker
        tracker = PatientTrackerWindows()
        tracker.start_tracking()
        
        print("Patient tracking started. Press Ctrl+C to stop.")
        print("This is a Windows test version with simulated GPS/GSM modules.")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print('\nShutting down patient tracking system...')
        tracker.cleanup()
    except Exception as e:
        print(f"Fatal error: {e}")
        if 'tracker' in locals():
            tracker.cleanup()
