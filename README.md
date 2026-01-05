# Patient Tracking System

A comprehensive patient tracking solution using Raspberry Pi Zero WH, SIM800L GSM module, and NEO-6M GPS module.

## Features

- **Real-time GPS tracking** with NEO-6M module
- **SMS alerts** via SIM800L GSM module
- **Geofence monitoring** with configurable safe zones
- **Web dashboard** for live tracking visualization
- **Local data storage** with SQLite database
- **Auto-start service** on boot
- **Alert management** system

## Hardware Requirements

- Raspberry Pi Zero WH
- SIM800L GSM Module
- NEO-6M GPS Module
- MicroSD Card (16GB+)
- Power Bank or 5V 2A Power Supply
- Jumper Wires
- External GSM and GPS antennas
- Activated SIM card with data plan

## Software Requirements

- Raspberry Pi OS Lite
- Python 3.7+
- Required packages (see requirements.txt)

## Quick Start

### 1. Hardware Setup

Follow the detailed wiring instructions in `HARDWARE_SETUP.md`.

**Important Notes:**
- SIM800L requires external 5V 2A power supply
- Use level shifters for GSM module connections
- GPS antenna needs clear sky view
- Only one device can use UART at a time

### 2. Software Installation

1. Clone or copy all files to Raspberry Pi
2. Make install script executable: `chmod +x install.sh`
3. Run installation: `./install.sh`
4. Reboot when prompted

### 3. Configuration

Edit `config.json` to customize:
- Patient ID
- Emergency phone numbers
- Geofence coordinates and radius
- Update intervals
- Server URL (optional)

### 4. Start System

The system starts automatically after boot. To manually control:

```bash
# Check status
sudo systemctl status patient-tracker

# Start service
sudo systemctl start patient-tracker

# Stop service
sudo systemctl stop patient-tracker

# View logs
sudo journalctl -u patient-tracker -f
```

### 5. Web Dashboard

Access the web dashboard at:
- Local: `http://raspberry-pi-ip:5000`
- Run with: `python3 web_dashboard.py`

## File Structure

```
patient_tracker/
├── patient_tracker.py      # Main tracking application
├── web_dashboard.py        # Web dashboard server
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── install.sh            # Installation script
├── HARDWARE_SETUP.md     # Hardware wiring guide
├── README.md             # This file
├── templates/
│   └── dashboard.html    # Web dashboard UI
└── patient_tracking.db   # SQLite database (auto-created)
```

## Configuration Options

### Basic Settings
- `patient_id`: Unique patient identifier
- `gps_port`: GPS serial port
- `gsm_port`: GSM serial port
- `update_interval`: Location update frequency (seconds)

### Geofence
- `enabled`: Enable/disable geofence
- `latitude/longitude`: Safe zone center
- `radius`: Safe zone radius (meters)

### Emergency Contacts
- `emergency_numbers`: List of phone numbers for SMS alerts

## Troubleshooting

### GPS Issues
- Ensure antenna has clear sky view
- Wait 2-5 minutes for satellite lock
- Check serial port permissions
- Verify baud rate (9600 for NEO-6M)

### GSM Issues
- Check SIM card activation
- Verify power supply (5V 2A minimum)
- Ensure antenna connection
- Check network coverage

### Serial Port Conflicts
- Only one device can use UART at a time
- Use USB to TTL converter for second device
- Disable Bluetooth serial: `dtoverlay=pi3-miniuart-bt`

### Service Issues
```bash
# Check service status
sudo systemctl status patient-tracker

# View error logs
sudo journalctl -u patient-tracker --no-pager

# Restart service
sudo systemctl restart patient-tracker
```

## API Endpoints

The web dashboard provides these API endpoints:

- `GET /api/current_location` - Current patient location
- `GET /api/location_history` - Location history (last 24h)
- `GET /api/alerts` - Active alerts
- `POST /api/mark_alert_resolved` - Mark alert as resolved
- `GET /api/geofence_status` - Geofence status
- `GET /api/statistics` - System statistics

## Data Storage

- **SQLite Database**: Local storage of locations and alerts
- **Automatic Cleanup**: Old data removed based on retention settings
- **Export**: Database can be exported for analysis

## Security Considerations

- Change default passwords
- Use HTTPS for remote dashboard access
- Secure SIM card with PIN
- Regular system updates
- Monitor system logs

## Power Management

- Use high-quality power bank for mobile use
- Monitor battery levels
- Consider solar charging for extended deployment
- Configure sleep modes to conserve power

## Support

For issues and questions:
1. Check hardware connections
2. Review system logs
3. Verify configuration
4. Test individual components
5. Check network connectivity

## License

This project is provided as-is for educational and medical monitoring purposes. Ensure compliance with local regulations and patient privacy requirements.
