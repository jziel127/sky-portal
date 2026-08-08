"""
SkyPortal Hardware Calibration & Range Finder
----------------------------------------------
Manually adjust individual servos to discover mechanical hard-stops,
tune the Photon Knob limits, and prevent motor buzzing/stall current.

Author: SkyPortal Project
"""

import sys
import os
import time
import serial

# Default COM Port and Baud
SERIAL_PORT = "COM7"
BAUD_RATE = 9600

def init_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2)
        print(f"\n[CONNECTED] Opened hardware connection on {port}")
        return ser
    except Exception as e:
        print(f"\n[SERIAL ERROR] Could not open {port}: {e}")
        return None

def send_cmd(ser, pwr, pho, col):
    if ser and ser.is_open:
        cmd = f"SET {int(pwr)} {int(pho)} {int(col)}\n"
        try:
            ser.write(cmd.encode('ascii'))
            time.sleep(0.05)
            rx = ser.read_all().decode('ascii', errors='ignore').strip()
            print(f"  [TX] -> SET Power:{pwr}° | Photon:{pho}° | Ratio:{col}°  (Hardware RX: {rx})")
        except Exception as e:
            print(f"  [SERIAL ERROR] {e}")

def main():
    print("=======================================================")
    print("     SKYPORTAL SERVO CALIBRATION & RANGE TESTER        ")
    print("=======================================================")

    ser = init_serial(SERIAL_PORT, BAUD_RATE)
    if not ser:
        return

    # Baseline safe starting positions
    pwr, pho, col = 90, 90, 90
    send_cmd(ser, pwr, pho, col)

    while True:
        print("\n-------------------------------------------------------")
        print(f" CURRENT POSITIONS -> [Power: {pwr}°] [Photon: {pho}°] [Ratio: {col}°]")
        print("-------------------------------------------------------")
        print("  [1] Adjust Photon Servo (D9) ONLY ")
        print("  [2] Adjust Power Servo (D11) ONLY")
        print("  [3] Adjust Color Ratio Servo (D10) ONLY")
        print("  [4] Sweep ALL Servos Together")
        print("  [5] Test Full Min/Max Range (10° -> 90° -> 170°)")
        print("  [q] Quit & Relieve Tension (Park at 10°)")
        print("-------------------------------------------------------")

        choice = input("Select an option: ").strip().lower()

        if choice == 'q':
            print("\nParking all servos at safe 10° position...")
            send_cmd(ser, 10, 10, 10)
            ser.close()
            break

        elif choice == '1':
            val = input("Enter target angle for PHOTON SERVO (0 - 180): ").strip()
            if val.isdigit() and 0 <= int(val) <= 180:
                pho = int(val)
                send_cmd(ser, pwr, pho, col)

        elif choice == '2':
            val = input("Enter target angle for POWER SERVO (0 - 180): ").strip()
            if val.isdigit() and 0 <= int(val) <= 180:
                pwr = int(val)
                send_cmd(ser, pwr, pho, col)

        elif choice == '3':
            val = input("Enter target angle for COLOR RATIO SERVO (0 - 180): ").strip()
            if val.isdigit() and 0 <= int(val) <= 180:
                col = int(val)
                send_cmd(ser, pwr, pho, col)

        elif choice == '4':
            val = input("Enter uniform angle for ALL 3 SERVOS (0 - 180): ").strip()
            if val.isdigit() and 0 <= int(val) <= 180:
                pwr = pho = col = int(val)
                send_cmd(ser, pwr, pho, col)

        elif choice == '5':
            print("\nRunning Min/Mid/Max Sweep...")
            for test_angle in [10, 90, 170]:
                print(f"\nMoving all servos to {test_angle}°...")
                pwr = pho = col = test_angle
                send_cmd(ser, pwr, pho, col)
                time.sleep(3)

if __name__ == "__main__":
    main()