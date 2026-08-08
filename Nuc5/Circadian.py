"""
SkyPortal Circadian Engine (Background Service)
-----------------------------------------------
Fetches real-time weather and updates physical hardware servo positions via COM7.

Channel Mapping:
- Power (pwr): 10° OFF, 180° ON
- Photon Intensity (pho): 10° (Dim) to 180° (Max Intensity)
- Color Ratio (col): 5° (Pure Warm Red) to 170° (Cool White)

Author: SkyPortal Project
"""

import sys
import os
import time
import requests
import serial
from datetime import datetime

# Path import fix
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from config import API_KEY, LAT, LON
except ImportError:
    print("[CIRCADIAN WARN] Could not import config.py - using fallbacks.")
    API_KEY, LAT, LON = "YOUR_API_KEY_HERE", 43.13, -88.22

SERIAL_PORT = "COM7"
BAUD_RATE = 9600
POLL_INTERVAL_SEC = 300  # Poll every 5 minutes


def init_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2)
        print(f"[CIRCADIAN] Connected to Hardware on {port}")
        return ser
    except Exception as e:
        print(f"[CIRCADIAN WARN] Serial bypass ({port}): {e}")
        return None


def fetch_weather(session):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial"
    )
    resp = session.get(url, timeout=8)
    resp.raise_for_status()
    data = resp.json()

    clouds = data.get("clouds", {}).get("all", 0)
    temp = round(data.get("main", {}).get("temp", 70))
    condition = data.get("weather", [{}])[0].get("main", "Clear")

    return clouds, condition, temp


def calculate_servo_angles(hour, clouds, condition):
    is_daytime = 6 <= hour < 21
    pwr = 180 if is_daytime else 10

    if not is_daytime:
        return pwr, 10, 10

    # Solar progress factor (0.0 at dawn/dusk, 1.0 at noon)
    if hour < 13:
        solar_progress = (hour - 6) / 7.0
    else:
        solar_progress = (21 - hour) / 8.0

    solar_progress = max(0.0, min(1.0, solar_progress))

    # 1. Photon Intensity (pho): 20° to 180°
    cloud_factor = (100 - clouds) / 100.0
    pho = int(20 + (160 * solar_progress * cloud_factor))
    pho = max(10, min(180, pho))

    # 2. Color Ratio (col): 5° (Pure Warm Red) to 170° (Cool White)
    col = int(5 + (165 * solar_progress))

    # Overcast/Storm override
    if condition in ["Rain", "Thunderstorm", "Drizzle", "Clouds"] and clouds > 75:
        col = max(15, int(col * 0.4))
        pho = max(20, int(pho * 0.5))

    col = max(5, min(170, col))

    return pwr, pho, col


def send_servo_cmd(ser, pwr, pho, col):
    if ser and ser.is_open:
        cmd = f"SET {int(pwr)} {int(pho)} {int(col)}\n"
        try:
            ser.write(cmd.encode('ascii'))
            time.sleep(0.1)
            rx = ser.read_all().decode('ascii', errors='ignore').strip()
            print(f"  [TX] -> {cmd.strip()} | RX <- {rx}")
        except Exception as e:
            print(f"  [SERIAL ERROR] {e}")


def main():
    print("=======================================================")
    print("             SKYPORTAL CIRCADIAN ENGINE                ")
    print("=======================================================")

    ser = init_serial(SERIAL_PORT, BAUD_RATE)
    session = requests.Session()

    while True:
        try:
            now = datetime.now()
            hour = now.hour

            clouds, condition, temp = fetch_weather(session)
            print(f"\n[{now.strftime('%H:%M:%S')}] Weather: {condition} ({clouds}% clouds) | Temp: {temp}°F")

            pwr, pho, col = calculate_servo_angles(hour, clouds, condition)
            print(f"  Target Angles -> Power:{pwr}° | Photon Intensity:{pho}° | Color Ratio:{col}°")

            send_servo_cmd(ser, pwr, pho, col)

        except Exception as e:
            print(f"  [CIRCADIAN ERROR] {e}")

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()