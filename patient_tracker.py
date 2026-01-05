#!/usr/bin/env python3
"""
Patient Tracking System using Raspberry Pi Zero WH, SIM800L GSM Module, and NEO-6M GPS Module
Author: Patient Tracking System
Date: 2025
"""

import serial
import time
import json
import sqlite3
import threading
import logging
from datetime import datetime
import pynmea2
import requests
import os
from signal import signal, SIGINT
from sys import exit

class PatientTracker:
    def __init__(self):
        # Configuration
        self.config = self.load_config()
        
        # Serial ports
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
            # Default configuration
            default_config = {
                "patient_id": "PATIENT001",
                "gps_port": "/dev/ttyS0",
                "gps_baudrate": 9600,
                "gsm_port": "/dev/ttyUSB0",
                "gsm_baudrate": 115200,
                "server_url": "http://your-server.com/api/location",
                "update_interval": 30,
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
        """Initialize GPS and GSM serial connections"""
        try:
            # Initialize GPS
            self.gps_port = serial.Serial(
                self.config['gps_port'],
                self.config['gps_baudrate'],
                timeout=1
            )
            self.logger.info(f"GPS initialized on {self.config['gps_port']}")
            
            # Initialize GSM
            self.gsm_port = serial.Serial(
                self.config['gsm_port'],
                self.config['gsm_baudrate'],
                timeout=1
            )
            self.logger.info(f"GSM initialized on {self.config['gsm_port']}")
            
            # Test GSM module
            self.test_gsm_module()
            
        except Exception as e:
            self.logger.error(f"Serial port initialization failed: {e}")
            raise
    
    def test_gsm_module(self):
        """Test GSM module connectivity"""
        try:
            self.send_gsm_command('AT')
            response = self.send_gsm_command('ATI')
            self.logger.info(f"GSM Module Info: {response}")
            
            # Check signal strength
            signal_strength = self.send_gsm_command('AT+CSQ')
            self.logger.info(f"Signal Strength: {signal_strength}")
            
            # Set SMS mode to text
            self.send_gsm_command('AT+CMGF=1')
            
        except Exception as e:
            self.logger.error(f"GSM module test failed: {e}")
            raise
    
    def send_gsm_command(self, command, wait_time=1):
        """Send command to GSM module and return response"""
        try:
            self.gsm_port.write((command + '\r\n').encode())
            time.sleep(wait_time)
            response = ''
            while self.gsm_port.in_waiting > 0:
                response += self.gsm_port.read(self.gsm_port.in_waiting).decode()
            return response.strip()
        except Exception as e:
            self.logger.error(f"GSM command failed: {command} - {e}")
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
            self.logger.error(f"GPS parsing error: {e}")
        return None
    
    def get_gps_location(self):
        """Get current GPS location"""
        try:
            if self.gps_port.in_waiting > 0:
                gps_data = self.gps_port.read(self.gps_port.in_waiting).decode()
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
                location.get('speed'),
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
            import math
            
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
        """Trigger alert and send notifications"""
        try:
            # Store alert in database
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO alerts 
                (patient_id, alert_type, message, latitude, longitude, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.patient_id, alert_type, message, latitude, longitude, datetime.now()))
            self.db_conn.commit()
            
            # Send SMS alerts
            for number in self.config['emergency_numbers']:
                self.send_sms_alert(number, f"ALERT: {message}")
            
            self.logger.warning(f"Alert triggered: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Alert triggering failed: {e}")
    
    def send_sms_alert(self, phone_number, message):
        """Send SMS alert via GSM module"""
        try:
            self.send_gsm_command(f'AT+CMGS="{phone_number}"', wait_time=2)
            self.gsm_port.write((message + '\x1A').encode())
            time.sleep(2)
            response = self.send_gsm_command('', wait_time=2)
            self.logger.info(f"SMS sent to {phone_number}: {message}")
        except Exception as e:
            self.logger.error(f"SMS sending failed: {e}")
    
    def upload_to_server(self, location):
        """Upload location data to server"""
        try:
            if not self.config.get('server_url'):
                return
            
            data = {
                'patient_id': self.patient_id,
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'altitude': location.get('altitude'),
                'timestamp': location['timestamp'].isoformat(),
                'speed': location.get('speed')
            }
            
            response = requests.post(
                self.config['server_url'],
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Location uploaded to server successfully")
            else:
                self.logger.warning(f"Server upload failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Server upload error: {e}")
    
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
                    
                    # Upload to server
                    self.upload_to_server(location)
                    
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

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\nShutting down patient tracking system...')
    tracker.cleanup()
    exit(0)

if __name__ == "__main__":
    # Setup signal handler
    signal(SIGINT, signal_handler)
    
    try:
        # Create and start tracker
        tracker = PatientTracker()
        tracker.start_tracking()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        tracker.cleanup()
        exit(1)
