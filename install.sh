#!/bin/bash

# Patient Tracking System Installation Script
# For Raspberry Pi Zero WH

echo "=== Patient Tracking System Installation ==="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "Installing Python and pip..."
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install git sqlite3 gpsd gpsd-clients minicom -y

# Enable serial port
echo "Configuring serial port..."
sudo raspi-config nonint do_serial 2
echo "enable_uart=1" | sudo tee -a /boot/config.txt
echo "dtoverlay=pi3-miniuart-bt" | sudo tee -a /boot/config.txt

# Create project directory
echo "Setting up project directory..."
PROJECT_DIR="/home/pi/patient_tracker"
sudo mkdir -p $PROJECT_DIR
sudo chown pi:pi $PROJECT_DIR

# Copy files to project directory
echo "Copying project files..."
cp patient_tracker.py $PROJECT_DIR/
cp config.json $PROJECT_DIR/
cp requirements.txt $PROJECT_DIR/

# Install Python dependencies
echo "Installing Python dependencies..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/patient-tracker.service > /dev/null <<EOF
[Unit]
Description=Patient Tracking System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python patient_tracker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable patient-tracker.service
sudo systemctl start patient-tracker.service

# Create device links
echo "Creating device links..."
sudo ln -sf /dev/ttyS0 /dev/gps0
sudo ln -sf /dev/ttyUSB0 /dev/gsm0

# Add user to dialout group
echo "Adding user to dialout group..."
sudo usermod -a -G dialout pi

# Create log directory
echo "Creating log directory..."
sudo mkdir -p /var/log/patient_tracker
sudo chown pi:pi /var/log/patient_tracker

# Setup complete
echo "=== Installation Complete ==="
echo "Reboot is required to apply all changes."
echo "After reboot, the tracking system will start automatically."
echo "Check status with: sudo systemctl status patient-tracker"
echo "View logs with: sudo journalctl -u patient-tracker -f"

read -p "Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo reboot
fi
