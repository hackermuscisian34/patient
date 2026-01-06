#!/bin/bash

echo "=================================="
echo "Patient Tracker - Raspberry Pi Setup"
echo "=================================="

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "    This script is designed for Raspberry Pi Zero WH"
    read -p "    Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Detected Raspberry Pi"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [[ $(echo "$python_version >= 3.7" | bc -l) -eq 1 ]]; then
    echo "✓ Python $python_version detected"
else
    echo "✗ Python 3.7+ required. Found: $python_version"
    exit 1
fi

# Install required packages
echo ""
echo "[INSTALL] Installing required packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-serial sqlite3

# Install Python packages
echo ""
echo "[PYTHON] Installing Python packages..."
pip3 install pyserial pynmea2 requests

# Check serial ports
echo ""
echo "[HARDWARE] Checking serial ports..."

# Check GPS port (ttyS0)
if [ -e /dev/ttyS0 ]; then
    echo "✓ GPS port /dev/ttyS0 found"
else
    echo "✗ GPS port /dev/ttyS0 not found"
    echo "  Make sure GPS is connected to GPIO pins 14 (TX) and 15 (RX)"
fi

# Check GSM port (ttyUSB0)
if [ -e /dev/ttyUSB0 ]; then
    echo "✓ GSM port /dev/ttyUSB0 found"
else
    echo "✗ GSM port /dev/ttyUSB0 not found"
    echo "  Make sure GSM module is connected via USB"
fi

# Check user permissions
echo ""
echo "[PERMISSIONS] Checking serial port permissions..."
if groups $USER | grep -q "dialout"; then
    echo "✓ User $USER is in dialout group"
else
    echo "✗ User $USER is not in dialout group"
    echo "  Adding user to dialout group..."
    sudo usermod -a -G dialout $USER
    echo "  ⚠️  You need to logout and login again for changes to take effect"
    echo "     Or run: newgrp dialout"
fi

# Enable serial port
echo ""
echo "[CONFIG] Enabling serial port..."
if sudo raspi-config nonint get_serial_hw | grep -q "0"; then
    echo "✓ Serial port already enabled"
else
    echo "Enabling serial port..."
    sudo raspi-config nonint do_serial_hw 0
    echo "✓ Serial port enabled"
fi

# Disable serial console (if enabled)
if sudo raspi-config nonint get_serial_cons | grep -q "1"; then
    echo "✓ Serial console already disabled"
else
    echo "Disabling serial console..."
    sudo raspi-config nonint do_serial_cons 1
    echo "✓ Serial console disabled"
fi

# Create systemd service
echo ""
echo "[SERVICE] Creating systemd service..."
sudo tee /etc/systemd/system/patient-tracker.service > /dev/null <<EOF
[Unit]
Description=Patient Tracking System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/patient_tracker_pi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service created"

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable patient-tracker.service

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To run the patient tracker:"
echo "  python3 patient_tracker_pi.py"
echo ""
echo "To start as service:"
echo "  sudo systemctl start patient-tracker"
echo ""
echo "To check service status:"
echo "  sudo systemctl status patient-tracker"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u patient-tracker -f"
echo ""
echo "Hardware connections:"
echo "  GPS: GPIO 14 (TX) and GPIO 15 (RX)"
echo "  GSM: USB port"
echo ""
echo "⚠️  If you just added user to dialout group,"
echo "    logout and login again before running!"
echo ""
