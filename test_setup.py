#!/usr/bin/env python3
"""
Simple test to verify the patient tracker setup
"""
import json
import os
import sqlite3
from datetime import datetime

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        print(f"✓ Config loaded successfully")
        print(f"  GPS Port: {config['gps_port']}")
        print(f"  GSM Port: {config['gsm_port']}")
        print(f"  Patient ID: {config['patient_id']}")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\nTesting database...")
    try:
        conn = sqlite3.connect('patient_tracking.db')
        cursor = conn.cursor()
        
        # Test table creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                latitude REAL,
                longitude REAL,
                timestamp DATETIME
            )
        ''')
        
        # Test insert
        cursor.execute('''
            INSERT INTO test_locations (patient_id, latitude, longitude, timestamp)
            VALUES (?, ?, ?, ?)
        ''', ('TEST001', 40.7128, -74.0060, datetime.now()))
        
        conn.commit()
        
        # Test select
        cursor.execute('SELECT COUNT(*) FROM test_locations')
        count = cursor.fetchone()[0]
        
        print(f"✓ Database working - {count} test records")
        
        # Clean up
        cursor.execute('DROP TABLE test_locations')
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_serial_ports():
    """Test serial port availability"""
    print("\nTesting serial ports...")
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        print(f"✓ Found {len(ports)} serial ports:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
        return True
    except Exception as e:
        print(f"✗ Serial port error: {e}")
        return False

def main():
    print("Patient Tracker Setup Test")
    print("=" * 40)
    
    tests = [
        test_config,
        test_database, 
        test_serial_ports
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✓ All tests passed! You can run the patient tracker.")
        print("\nTo run the Windows test version:")
        print("  python patient_tracker_windows.py")
        print("\nTo run the original version (requires hardware):")
        print("  python patient_tracker.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
