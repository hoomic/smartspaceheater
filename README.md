# Smart Space Heater Web Controller

A Python web interface for controlling a space heater via a smart plug and Raspberry Pi temperature sensor.

## Features

- **Real-time temperature monitoring** - Displays current temperature from sensor
- **Automatic temperature control** - Maintains target temperature with hysteresis
- **Manual override mode** - Direct heater on/off control
- **Temperature history chart** - Visual representation of recent temperature readings
- **Mobile-responsive interface** - Works on phones, tablets, and desktops
- **RESTful API** - Easy integration with other systems

## Requirements

- Raspberry Pi (any model with GPIO)
- Temperature sensor (DS18B20 recommended)
- Smart plug (compatible with your setup)
- Python 3.7+

## Installation

1. Install Python dependencies:
```bash
pip install flask
```

2. Install additional dependencies based on your hardware:

**For DS18B20 temperature sensor:**
```bash
# Enable 1-Wire interface
sudo raspi-config
# Navigate to: Interface Options -> 1-Wire -> Enable

# No additional Python packages needed (uses /sys/bus/w1/devices/)
```

**For TP-Link Kasa smart plugs:**
```bash
pip install python-kasa
```

**For Tuya-based smart plugs:**
```bash
pip install tinytuya
```

**For other smart plugs:**
- Check manufacturer documentation for Python libraries

3. Clone or download this project to your Raspberry Pi

## Configuration

### Temperature Sensor Setup

The default code includes a simulated temperature sensor. Replace the `read_temperature()` function in `heater_control.py` with your actual sensor code.

**Example for DS18B20 sensor:**

```python
def read_temperature():
    import glob
    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
    
    with open(device_file, 'r') as f:
        lines = f.readlines()
    
    if lines[0].strip()[-3:] == 'YES':
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            return float(temp_string) / 1000.0
    return None
```

### Smart Plug Setup

Replace the `control_heater()` function with your smart plug control code.

**Example for TP-Link Kasa:**

```python
def control_heater(turn_on):
    from kasa import SmartPlug
    import asyncio
    
    plug = SmartPlug("192.168.1.100")  # Replace with your plug's IP
    
    async def control():
        await plug.update()
        if turn_on:
            await plug.turn_on()
        else:
            await plug.turn_off()
    
    asyncio.run(control())
    
    with config.lock:
        config.heater_on = turn_on
```

**Example for Tuya:**

```python
def control_heater(turn_on):
    import tinytuya
    
    d = tinytuya.OutletDevice(
        dev_id='YOUR_DEVICE_ID',
        address='192.168.1.100',  # Your plug's IP
        local_key='YOUR_LOCAL_KEY',
        version=3.3
    )
    
    d.set_status(turn_on)
    
    with config.lock:
        config.heater_on = turn_on
```

## Usage

1. Start the server:
```bash
python3 heater_control.py
```

2. Access the web interface:
- From the Pi: http://localhost:5000
- From another device on the network: http://[PI_IP_ADDRESS]:5000
  (Find your Pi's IP with: `hostname -I`)

3. Control your heater:
- Set target temperature using +/- buttons
- Switch between Automatic and Manual modes
- In Manual mode, directly control heater on/off

## API Endpoints

### GET /api/status
Returns current system status:
```json
{
  "current_temp": 21.5,
  "target_temp": 22.0,
  "heater_on": true,
  "auto_mode": true,
  "temp_history": [...]
}
```

### POST /api/set_target
Set target temperature:
```json
{
  "target": 23.0
}
```

### POST /api/set_mode
Set control mode:
```json
{
  "auto": true
}
```

### POST /api/set_heater
Manual heater control (manual mode only):
```json
{
  "on": true
}
```

## Safety Features

- Temperature limits: 10-30°C range
- Hysteresis control: ±0.5°C to prevent rapid cycling
- Thread-safe operations with locks
- Automatic mode prevents accidental manual control

## Running on Startup

To start the heater controller automatically on boot:

1. Create a systemd service file:
```bash
sudo nano /etc/systemd/system/heater-control.service
```

2. Add the following content:
```ini
[Unit]
Description=Smart Heater Control
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/heater_control
ExecStart=/usr/bin/python3 /home/pi/heater_control/heater_control.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl enable heater-control.service
sudo systemctl start heater-control.service
```

4. Check status:
```bash
sudo systemctl status heater-control.service
```

## Troubleshooting

**Temperature reads as 0 or None:**
- Check DS18B20 sensor wiring (VCC, GND, Data)
- Verify 1-Wire is enabled: `lsmod | grep w1`
- Check sensor is detected: `ls /sys/bus/w1/devices/`

**Smart plug not responding:**
- Verify plug IP address is correct
- Check network connectivity
- Ensure plug is on the same network as Pi
- Check firewall settings

**Web interface not accessible:**
- Verify Flask is running: `ps aux | grep python`
- Check Pi's IP address: `hostname -I`
- Ensure port 5000 is not blocked by firewall

## Customization

- Adjust temperature check interval in `temperature_monitor()` (default: 5 seconds)
- Modify hysteresis values in automatic control logic (default: ±0.5°C)
- Change temperature range limits in `/api/set_target` (default: 10-30°C)
- Customize web interface colors in `templates/index.html`

## Security Notes

- This is designed for local network use only
- For internet access, implement authentication and HTTPS
- Consider using a reverse proxy (nginx) for production
- Keep smart plug firmware updated
- Use strong passwords for your network

## License

Free to use and modify for personal projects.
