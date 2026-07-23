# Sky Portal — Automated Circadian Lighting & Clock

A personal engineering project that adds automation and a companion display to a [Chroma Sky Portal 2.1](https://getchroma.co/) circadian light — without modifying the light itself.

## What it does

- **Automates the Sky Portal's settings** (brightness/"Photon" and color temperature/"Red-White Ratio") throughout the day, driven by real solar and weather data rather than a physical light sensor. Small external servos physically turn the light's existing knobs, so the device itself is never opened or altered.
- **Auto power on/off** via a third, higher-torque servo that physically flips the unit's power switch.
- **A companion 16x16 LED matrix** running [WLED](https://kno.wled.ge/) on an ESP32 shows a clock, the date, and the current outdoor weather (with a simple animated icon and temperature), cycling automatically.

## How it works (high level)

```
Windows mini PC (central brain)
   │  pulls solar elevation + cloud cover from OpenWeatherMap
   │  computes a "circadian phase" for the day
   │
   ├── USB Serial ──► Arduino Pro Mini ──► 3 servos (Photon, Color Ratio, Power)
   │
   └── HTTP/MQTT ──► ESP32 (WLED) ──► 16x16 LED matrix (clock + weather display)
```

## Hardware

- Chroma Sky Portal 2.1 (the light being automated)
- Windows mini PC (GMK NucBox5) — control logic, API calls
- Arduino Pro Mini + FTDI adapter — servo control
- 2x SG90 micro servos + 1x MG996R servo
- ESP32 + WS2812B 16x16 LED matrix, running WLED
- Custom 3D-printed enclosure housing the electronics, attached to the light's stand

## Status

Actively in progress — the LED matrix clock is fully built and running; the servo/knob automation is the current phase of work.

## Why this project exists

Built as a personal engineering/robotics project to combine embedded systems, API integration, and mechanical design into something used every day — not a commercial product, and not affiliated with Chroma.
