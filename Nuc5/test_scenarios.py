"""
SkyPortal Interactive Scenario Selector (Corrected Channel Mapping)
-------------------------------------------------------------------
Channel Rules:
- Power (pwr): System power state (0° OFF, 180° ON)
- Photon (pho): Light Intensity / Brightness
- Color Ratio (col): Red-to-White Ratio (5° Pure Red, 170° Pure White)

Author: SkyPortal Project
"""

import sys
import os
import time
import requests
import serial

# Dynamic Import Path Fix
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import API_KEY, LAT, LON
except ImportError:
    API_KEY, LAT, LON = "DUMMY", 0, 0

# --- Configuration Settings ---
SERIAL_PORT = "COM7"
BAUD_RATE = 9600
WLED_IP = "192.168.1.209"

# --- Defined Weather Test Profiles ---
SCENARIOS = {
    "1": {
        "name": "Dawn / Sunrise (Dim Warm Red)",
        "pwr": 180, "pho": 35, "col": 5,
        "desc": "Power ON, Dim Intensity (pho=35°), Pure Red (col=5°)",
    },
    "2": {
        "name": "Mid-Morning Clear Sky",
        "pwr": 180, "pho": 170, "col": 77,
        "desc": "Power ON, High Intensity (pho=170°), Mid Spectrum (col=77°)",
    },
    "3": {
        "name": "Solar Noon (Peak Bright White)",
        "pwr": 180, "pho": 180, "col": 170,
        "desc": "Power ON, Max Intensity (pho=180°), Cool White (col=170°)",
    },
    "4": {
        "name": "Heavy Overcast / Storm (Dim Deep Red)",
        "pwr": 180, "pho": 20, "col": 15,
        "desc": "Power ON, Very Dim (pho=20°), Deep Red (col=15°)",
    },
    "5": {
        "name": "Golden Hour / Sunset (PURE BRIGHT RED)",
        "pwr": 180, "pho": 165, "col": 5,
        "desc": "Power ON, High Intensity (pho=165°), PURE RED (col=5°)",
    },
    "6": {
        "name": "Night Mode (System Off / Parked)",
        "pwr": 10, "pho": 10, "col": 10,
        "desc": "Power OFF (10°), Zero Intensity (10°), Parked Spectrum (10°)",
    },
}

# --- Hardware Drivers ---

def init_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2)
        print(f" Connected to SkyPortal Hardware on {port}\n")
        return ser
    except Exception as e:
        print(f" Serial connection bypass ({port} not found): {e}\n")
        return None


def send_servo_cmd(ser, pwr, pho, col):
    if ser and ser.is_open:
        cmd = f"SET {int(pwr)} {int(pho)} {int(col)}\n"
        try:
            ser.write(cmd.encode('ascii'))
            time.sleep(0.1)
            rx = ser.read_all().decode('ascii', errors='ignore').strip()
            print(f"    [HARDWARE TX] -> {cmd.strip()} | RX <- {rx}")
        except Exception as e:
            print(f"    [SERIAL ERROR] {e}")


def sync_wled_preview(session, pwr, pho, col):
    """Sends matching color/brightness preview to WLED matrix."""
    # col: 5° (Red) to 170° (White)
    ratio = (col - 5) / 165.0
    r = 255
    g = int(80 + (155 * ratio))
    b = int(10 * ratio)
    brightness = int((pho / 180.0) * 255) if pwr > 10 else 0

    payload = {
        "on": pwr > 10,
        "bri": brightness,
        "seg": [{"id": 0, "col": [[r, g, b]]}]
    }

    try:
        url = f"http://{WLED_IP}/json/state"
        session.post(url, json=payload, timeout=3)
    except Exception:
        pass


def display_menu():
    print("=======================================================")
    print("      SKYPORTAL INTERACTIVE HARDWARE SCENARIO TESTER   ")
    print("=======================================================")
    for key, sc in SCENARIOS.items():
        print(f"  [{key}] {sc['name']}")
    print("  [q] Quit & Park Servos")
    print("-------------------------------------------------------")


def execute_scenario(key, ser, session):
    sc = SCENARIOS[key]
    print(f"\n Triggering Option [{key}]: {sc['name']}")
    print(f"   Details: {sc['desc']}")

    pwr, pho, col = sc["pwr"], sc["pho"], sc["col"]
    print(f"   Calculated Target -> Power: {pwr}°, Photon Intensity: {pho}°, Color Ratio: {col}°")

    send_servo_cmd(ser, pwr, pho, col)
    sync_wled_preview(session, pwr, pho, col)
    print(" State dispatched successfully.\n")


def main():
    ser = init_serial(SERIAL_PORT, BAUD_RATE)
    session = requests.Session()

    try:
        while True:
            display_menu()
            choice = input("Select a scenario number (1-6) or 'q': ").strip().lower()

            if choice == 'q':
                print("\n Exiting and parking hardware...")
                send_servo_cmd(ser, 10, 10, 10)
                break
            elif choice in SCENARIOS:
                execute_scenario(choice, ser, session)
            else:
                print("\n Invalid selection! Please enter 1, 2, 3, 4, 5, 6, or q.\n")

    except KeyboardInterrupt:
        print("\n Program interrupted. Parking hardware...")
        send_servo_cmd(ser, 10, 10, 10)
    finally:
        if ser and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()