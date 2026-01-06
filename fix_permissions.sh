#!/bin/bash

echo "=================================="
echo "Fix Serial Port Permissions"
echo "=================================="

# Get current user
USER=$(whoami)
echo "Current user: $USER"

# Check if user is in dialout group
if groups $USER | grep -q "dialout"; then
    echo "✓ User $USER is already in dialout group"
else
    echo "✗ User $USER is NOT in dialout group"
    echo "Adding user to dialout group..."
    sudo usermod -a -G dialout $USER
    echo "✓ User added to dialout group"
fi

# Check /dev/ttyS0 permissions
echo ""
echo "Checking /dev/ttyS0 permissions:"
ls -l /dev/ttyS0

# Add user to dialout group for current session
echo ""
echo "Applying permissions for current session..."
sudo usermod -a -G dialout $USER

# Try to change group ownership of serial port
echo ""
echo "Setting serial port permissions..."
sudo chmod 666 /dev/ttyS0 2>/dev/null || echo "Could not change /dev/ttyS0 permissions"

# Alternative: add to gpio group as well
sudo usermod -a -G gpio $USER 2>/dev/null

echo ""
echo "=================================="
echo "SOLUTIONS:"
echo "=================================="
echo ""
echo "1. RECOMMENDED: Logout and login again"
echo "   This will apply the group membership changes"
echo ""
echo "2. QUICK FIX: Run this command in current terminal:"
echo "   newgrp dialout"
echo "   Then run your Python script"
echo ""
echo "3. TEMPORARY FIX: Run with sudo:"
echo "   sudo python3 patient_tracker_pi.py"
echo ""
echo "4. PERMANENT FIX: Add to /etc/rc.local:"
echo "   sudo chmod 666 /dev/ttyS0"
echo ""
echo "After applying one of these solutions, run:"
echo "python3 patient_tracker_pi.py"
echo ""
