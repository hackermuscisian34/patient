#!/usr/bin/env python3
"""Test script to check serial port availability"""

import serial
import json

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_serial_ports():
    config = load_config()
    if not config:
        return
    
    print(f"Testing GPS port: {config['gps_port']}")
    try:
        gps_port = serial.Serial(config['gps_port'], config['gps_baudrate'], timeout=1)
        print(f"✓ GPS port {config['gps_port']} opened successfully")
        gps_port.close()
    except Exception as e:
        print(f"✗ GPS port {config['gps_port']} failed: {e}")
    
    print(f"Testing GSM port: {config['gsm_port']}")
    try:
        gsm_port = serial.Serial(config['gsm_port'], config['gsm_baudrate'], timeout=1)
        print(f"✓ GSM port {config['gsm_port']} opened successfully")
        gsm_port.close()
    except Exception as e:
        print(f"✗ GSM port {config['gsm_port']} failed: {e}")

if __name__ == "__main__":
    test_serial_ports()
