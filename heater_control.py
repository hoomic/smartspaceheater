#!/usr/bin/env python3
"""
Smart Space Heater Web Controller
Monitors temperature and automatically controls a heater via smart plug
"""

from flask import Flask, render_template, request, jsonify
import threading
import time
from datetime import datetime
import tinytuya
import board
import adafruit_dht

app = Flask(__name__)

def C2F(t):
    return t * 9 / 5 + 32

DEVICE_ID, DEVICE_IP, LOCAL_KEY = open("./plug_creds.txt").read().split()

SMART_PLUG = tinytuya.OutletDevice(DEVICE_ID, DEVICE_IP, LOCAL_KEY)
SMART_PLUG.set_version(3.5)

TEMP_SENSOR = adafruit_dht.DHT11(board.D4)

# Configuration
class HeaterConfig:
    def __init__(self):
        self.current_temp = 64.0  # Current temperature in Fahrenheit
        self.target_temp = 66.0   # Target temperature in Fahrenheit
        self.heater_on = False    # Heater state
        self.auto_mode = True     # Automatic control enabled
        self.temp_history = []    # Temperature history
        self.lock = threading.Lock()

config = HeaterConfig()

# Temperature sensor interface (replace with your actual sensor code)
def read_temperature():
    """
    Replace this with your actual temperature sensor code.
    Example for DS18B20 sensor:
    
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
    """
    # Simulated temperature reading - replace with actual sensor
    return C2F(TEMP_SENSOR.temperature)

# Smart plug interface (replace with your actual smart plug control code)
def control_heater(turn_on):
    """
    Replace this with your actual smart plug control code.
    Examples:
    
    For TP-Link Kasa smart plugs:
    from kasa import SmartPlug
    plug = SmartPlug("192.168.1.100")
    asyncio.run(plug.update())
    if turn_on:
        asyncio.run(plug.turn_on())
    else:
        asyncio.run(plug.turn_off())
    
    For Tuya-based plugs:
    import tinytuya
    d = tinytuya.OutletDevice('DEVICE_ID', 'IP_ADDRESS', 'LOCAL_KEY')
    d.set_status(turn_on)
    """
    # Simulated control - replace with actual smart plug code
    print(f"Heater turned {'ON' if turn_on else 'OFF'}")
    config.heater_on = turn_on
    if turn_on:
        SMART_PLUG.turn_on()
    else:
        SMART_PLUG.turn_off()

# Background temperature monitoring thread
def temperature_monitor():
    """Continuously monitor temperature and control heater"""
    while True:
        try:
            # Read current temperature
            temp = read_temperature()
            
            if temp is not None:
                with config.lock:
                    config.current_temp = temp
                    
                    # Store temperature history (keep last 100 readings)
                    config.temp_history.append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'temp': round(temp, 1)
                    })
                    if len(config.temp_history) > 100:
                        config.temp_history.pop(0)
                    
                    # Automatic temperature control
                    if config.auto_mode:
                        # Hysteresis: turn on 0.5°C below target, off 0.5°C above
                        if temp < config.target_temp - 0.5 and not config.heater_on:
                            control_heater(True)
                        elif temp > config.target_temp + 0.5 and config.heater_on:
                            control_heater(False)
            
        except Exception as e:
            print(f"Error in temperature monitor: {e}")
        
        time.sleep(5)  # Check every 5 seconds

# Web routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    with config.lock:
        return jsonify({
            'current_temp': round(config.current_temp, 1),
            'target_temp': round(config.target_temp, 1),
            'heater_on': config.heater_on,
            'auto_mode': config.auto_mode,
            'temp_history': config.temp_history[-20:]  # Last 20 readings
        })

@app.route('/api/set_target', methods=['POST'])
def set_target():
    """Set target temperature"""
    data = request.json
    target = float(data.get('target', 22))
        
    # Validate temperature range (10-30°C)
    if 50 <= target <= 85:
        with config.lock:
            config.target_temp = target
        return jsonify({'success': True, 'target_temp': target})
    else:
        return jsonify({'success': False, 'error': 'Temperature must be between 50-85°F'}), 400

@app.route('/api/set_mode', methods=['POST'])
def set_mode():
    """Set automatic/manual mode"""
    data = request.json
    auto = data.get('auto', True)
    
    with config.lock:
        config.auto_mode = auto
        
        # If switching to manual mode and heater is on, keep it on
        # User can manually control via set_heater endpoint
    
    return jsonify({'success': True, 'auto_mode': auto})

@app.route('/api/set_heater', methods=['POST'])
def set_heater():
    """Manually control heater (only in manual mode)"""
    data = request.json
    turn_on = data.get('on', False)
    
    with config.lock:
        if not config.auto_mode:
            control_heater(turn_on)
            return jsonify({'success': True, 'heater_on': turn_on})
        else:
            return jsonify({'success': False, 'error': 'Cannot manually control in auto mode'}), 400

if __name__ == '__main__':
    # Start temperature monitoring thread
    monitor_thread = threading.Thread(target=temperature_monitor, daemon=True)
    monitor_thread.start()
    
    # Start web server
    # Use 0.0.0.0 to allow access from other devices on network
    app.run(host='0.0.0.0', port=5000, debug=False)
