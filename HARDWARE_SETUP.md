# Patient Tracking System - Hardware Setup Guide

## Components Required
- Raspberry Pi Zero WH
- SIM800L GSM Module
- NEO-6M GPS Module
- MicroSD Card (16GB+)
- Power Bank or 5V 2A Power Supply
- Jumper Wires
- Breadboard (optional)
- SIM Card (activated with data plan)
- External GSM Antenna
- External GPS Antenna

## Wiring Connections

### NEO-6M GPS Module to Raspberry Pi
```
GPS Module    ->    Raspberry Pi Zero WH
VCC           ->    3.3V (Pin 1)
GND           ->    GND (Pin 6)
TXD           ->    RXD (GPIO 15 - Pin 10)
RXD           ->    TXD (GPIO 14 - Pin 8)
```

### SIM800L GSM Module to Raspberry Pi
```
SIM800L       ->    Raspberry Pi Zero WH
VCC           ->    5V (Pin 2) - Use external power supply!
GND           ->    GND (Pin 9)
TXD           ->    RXD (GPIO 15 - Pin 10)
RXD           ->    TXD (GPIO 14 - Pin 8)
RST           ->    GPIO 4 (Pin 7)
```

## Important Notes

### Power Requirements
- **SIM800L requires 5V 2A power supply** - Do not power from Raspberry Pi 5V pin
- Use external power supply for SIM800L to avoid voltage drops
- GPS module can be powered from Raspberry Pi 3.3V

### Serial Port Configuration
- Both GPS and GSM modules use UART communication
- Raspberry Pi Zero WH has one UART interface (GPIO 14/15)
- **Solution**: Use a USB to TTL converter for one module, or use I2C GPS module

### Alternative Setup (Recommended)
```
GPS Module    ->    USB to TTL Converter    ->    Raspberry Pi USB Port
SIM800L       ->    GPIO 14/15 (UART)       ->    Raspberry Pi
```

## Step-by-Step Hardware Setup

### 1. Prepare Raspberry Pi
1. Flash Raspberry Pi OS Lite to microSD card
2. Enable SSH and configure WiFi
3. Boot up and update system

### 2. Connect GPS Module
1. Connect VCC to 3.3V pin
2. Connect GND to any GND pin
3. Connect TXD to GPIO 15 (RXD)
4. Connect RXD to GPIO 14 (TXD)
5. Attach GPS antenna in open sky area

### 3. Connect SIM800L Module
1. **IMPORTANT**: Connect VCC to external 5V 2A power supply
2. Connect GND to common ground with Raspberry Pi
3. Connect TXD to GPIO 15 (RXD) - Use level shifter!
4. Connect RXD to GPIO 14 (TXD) - Use level shifter!
5. Connect RST to GPIO 4 (optional)
6. Insert activated SIM card
7. Attach GSM antenna

### 4. Level Shifter Requirement
SIM800L uses 5V logic levels while Raspberry Pi uses 3.3V. Use a bidirectional logic level shifter:
```
SIM800L TX -> Level Shifter HV -> Level Shifter LV -> Raspberry Pi RX
SIM800L RX -> Level Shifter HV -> Level Shifter LV -> Raspberry Pi TX
```

## Software Configuration

### Enable Serial Port
```bash
# Disable serial console
sudo raspi-config
# Select Interface Options -> Serial Port -> Disable shell, enable serial

# Add to /boot/config.txt
enable_uart=1
dtoverlay=pi3-miniuart-bt
```

### Create Device Links
```bash
# Create symbolic links for easier access
sudo ln -s /dev/ttyS0 /dev/gps0
sudo ln -s /dev/ttyUSB0 /dev/gsm0
```

## Testing Hardware

### Test GPS Module
```bash
# Install GPS tools
sudo apt-get install gpsd gpsd-clients

# Test GPS
sudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock
gpsmon
```

### Test SIM800L Module
```bash
# Install serial terminal
sudo apt-get install minicom

# Test GSM
sudo minicom -D /dev/ttyUSB0 -b 115200
# Type AT and press Enter - should respond with OK
```

## Troubleshooting

### GPS Issues
- Ensure GPS antenna has clear view of sky
- Wait 2-5 minutes for initial satellite lock
- Check baud rate (9600 default for NEO-6M)

### SIM800L Issues
- Check SIM card is activated and has data plan
- Ensure adequate power supply (5V 2A minimum)
- Check antenna connection
- Verify network coverage

### Serial Port Conflicts
- Only one device can use UART at a time
- Use USB to TTL converter for second device
- Disable Bluetooth serial port if needed

## Power Management
- Use high-quality power bank for mobile operation
- Monitor battery levels
- Consider solar charging for extended use
- Implement sleep modes to conserve power

## Safety Considerations
- Secure all connections with electrical tape
- Use strain relief for cables
- Protect electronics from moisture
- Ensure proper ventilation to prevent overheating
