#!/bin/bash

echo "=================================="
echo "Patient Tracker - Quick Setup"
echo "Raspberry Pi Zero WH"
echo "=================================="

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-serial sqlite3
pip3 install pyserial pynmea2

# Fix permissions
echo "Fixing permissions..."
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyS0 2>/dev/null

echo ""
echo "=================================="
echo "READY TO RUN!"
echo "=================================="
echo ""
echo "Choose ONE of these commands:"
echo ""
echo "1. EASIEST (with sudo):"
echo "   sudo python3 simple_tracker.py"
echo ""
echo "2. PROPER FIX (logout required):"
echo "   logout"
echo "   # login again"
echo "   python3 simple_tracker.py"
echo ""
echo "3. CURRENT SESSION:"
echo "   newgrp dialout"
echo "   python3 simple_tracker.py"
echo ""
echo "Hardware connections:"
echo "  GPS TX -> GPIO 15 (RXD)"
echo "  GPS RX -> GPIO 14 (TXD)"
echo "  GPS VCC -> 3.3V"
echo "  GPS GND -> GND"
echo ""
