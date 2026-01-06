#!/usr/bin/env python3
"""
Hardware Test Script for Raspberry Pi Zero WH
Tests GPS and GSM module connectivity
"""

import serial
import time
import sys
import os

def test_gps():
    """Test GPS module on /dev/ttyS0"""
    print("=" * 50)
    print("GPS MODULE TEST")
    print("=" * 50)
    
    try:
        print("Connecting to GPS on /dev/ttyS0...")
        gps = serial.Serial('/dev/ttyS0', 9600, timeout=2)
        print("✓ GPS port opened successfully")
        
        print("Listening for GPS data (10 seconds)...")
        start_time = time.time()
        nmea_count = 0
        
        while time.time() - start_time < 10:
            if gps.in_waiting > 0:
                data = gps.read(gps.in_waiting).decode('ascii', errors='ignore')
                lines = data.strip().split('\n')
                for line in lines:
                    if line.startswith('$'):
                        nmea_count += 1
                        if line.startswith('$GPGGA') or line.startswith('$GPRMC'):
                            print(f"  📍 {line}")
                        elif nmea_count <= 5:  # Show first 5 NMEA sentences
                            print(f"  📡 {line}")
            time.sleep(0.1)
        
        if nmea_count > 0:
            print(f"✓ GPS working - received {nmea_count} NMEA sentences")
        else:
            print("✗ No GPS data received")
            print("  Check connections:")
            print("    GPS TX -> GPIO 15 (RXD)")
            print("    GPS RX -> GPIO 14 (TXD)")
            print("    GPS VCC -> 3.3V or 5V")
            print("    GPS GND -> GND")
        
        gps.close()
        return nmea_count > 0
        
    except serial.SerialException as e:
        print(f"✗ GPS connection failed: {e}")
        print("  Make sure:")
        print("    1. GPS is connected to GPIO 14/15")
        print("    2. User has permission to access /dev/ttyS0")
        print("    3. Serial port is enabled in raspi-config")
        return False
    except Exception as e:
        print(f"✗ GPS test failed: {e}")
        return False

def test_gsm():
    """Test GSM module on /dev/ttyUSB0"""
    print("\n" + "=" * 50)
    print("GSM MODULE TEST")
    print("=" * 50)
    
    try:
        print("Connecting to GSM on /dev/ttyUSB0...")
        gsm = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
        print("✓ GSM port opened successfully")
        
        # Test basic AT command
        print("Sending AT command...")
        gsm.write(b'AT\r\n')
        time.sleep(1)
        
        response = ''
        if gsm.in_waiting > 0:
            response = gsm.read(gsm.in_waiting).decode('ascii', errors='ignore')
        
        if 'OK' in response:
            print("✓ GSM module responding")
            
            # Get module info
            print("Getting module info...")
            gsm.write(b'ATI\r\n')
            time.sleep(1)
            
            if gsm.in_waiting > 0:
                info = gsm.read(gsm.in_waiting).decode('ascii', errors='ignore')
                print(f"  📱 {info.strip()}")
            
            # Check signal strength
            print("Checking signal strength...")
            gsm.write(b'AT+CSQ\r\n')
            time.sleep(1)
            
            if gsm.in_waiting > 0:
                signal = gsm.read(gsm.in_waiting).decode('ascii', errors='ignore')
                print(f"  📶 {signal.strip()}")
            
            print("✓ GSM module working")
            gsm.close()
            return True
        else:
            print("✗ GSM module not responding")
            print("  Response:", repr(response))
            print("  Check connections:")
            print("    GSM module connected via USB")
            print("    SIM card inserted")
            print("    Power supply adequate")
            gsm.close()
            return False
            
    except serial.SerialException as e:
        print(f"✗ GSM connection failed: {e}")
        print("  Make sure:")
        print("    1. GSM module is connected via USB")
        print("    2. User has permission to access /dev/ttyUSB0")
        print("    3. GSM module is powered on")
        return False
    except Exception as e:
        print(f"✗ GSM test failed: {e}")
        return False

def check_permissions():
    """Check user permissions for serial ports"""
    print("\n" + "=" * 50)
    print("PERMISSIONS CHECK")
    print("=" * 50)
    
    import os
    user = os.getenv('USER')
    
    # Check if user is in dialout group
    try:
        with open('/etc/group', 'r') as f:
            groups = f.read()
            if f'dialout:x:' in groups and user in groups:
                print(f"✓ User {user} is in dialout group")
            else:
                print(f"✗ User {user} is NOT in dialout group")
                print("  Run: sudo usermod -a -G dialout $USER")
                print("  Then logout and login again")
    except:
        print("✗ Could not check group membership")
    
    # Check serial port permissions
    for port in ['/dev/ttyS0', '/dev/ttyUSB0']:
        if os.path.exists(port):
            if os.access(port, os.R_OK | os.W_OK):
                print(f"✓ Can read/write {port}")
            else:
                print(f"✗ Cannot access {port}")
        else:
            print(f"✗ {port} does not exist")

def main():
    print("RASPBERRY PI ZERO WH - HARDWARE TEST")
    print("====================================")
    print("This script tests GPS and GSM module connectivity")
    print("Make sure hardware is connected before running")
    print()
    
    # Check permissions first
    check_permissions()
    
    # Test GPS
    gps_ok = test_gps()
    
    # Test GSM
    gsm_ok = test_gsm()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"GPS Module: {'✓ PASS' if gps_ok else '✗ FAIL'}")
    print(f"GSM Module: {'✓ PASS' if gsm_ok else '✗ FAIL'}")
    
    if gps_ok and gsm_ok:
        print("\n🎉 All tests passed! Ready to run patient tracker.")
        print("   Run: python3 patient_tracker_pi.py")
    else:
        print("\n⚠️  Some tests failed. Check hardware connections.")
        print("   Review the messages above for troubleshooting.")
    
    print("\nHardware Connections:")
    print("  GPS Module:")
    print("    VCC -> 3.3V or 5V")
    print("    GND -> GND")
    print("    TXD -> GPIO 15 (RXD)")
    print("    RXD -> GPIO 14 (TXD)")
    print("  GSM Module:")
    print("    USB -> Raspberry Pi USB port")
    print("    SIM card inserted")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
