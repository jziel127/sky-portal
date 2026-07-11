# Sky Portal Project — Journal Entry (Part 2)
**Date:** July 4, 2026 (continued)
**Session focus:** Architecture simplification (weather-API-driven, no physical light sensor), WLED/ESP32 decision, comprehensive status check

---

## Major Architecture Decision: No Physical Light Sensor

**Change:** Dropped the BH1750 ambient light sensor and the Pico W's role as a wireless sensor node. Circadian logic will be driven **entirely by OpenWeatherMap API data** (solar elevation, cloud cover, UV index) rather than fused with real-world lux readings.

**Why:** Simpler build, no sensor hardware to buy/mount near a window, one less wireless node to maintain.

**What this eliminates:**
- BH1750 sensor (no longer needed)
- Pico W's original job (reading BH1750, publishing lux over MQTT) — no longer needed
- Sensor fusion logic in the circadian-phase calculation — simplified to weather-data-only

**What survives from that work:**
- Mosquitto broker — kept running, will be used for the future tablet control panel (final project phase)
- Pico W hardware itself — currently idle, may be repurposed (see WLED/ESP32 section below)
- All infrastructure debugging from today (static IP, Python env, VS Code/MicroPico, Mega serial) — general-purpose, not wasted

---

## WLED / ESP32 Decision (LED Matrix Control)

**Trigger:** Found a YouTube video ("16x16 LED Matrix Setup with WLED and ESP32, BEST Enclosure Design") demonstrating WLED firmware + ESP32 + a 3D-printed enclosure for a 16x16 WS2812B matrix — directly applicable to the Sky Portal desk display.

**Investigated:** Whether the already-owned Raspberry Pi Pico W could run WLED instead of buying new hardware.

**Finding:** WLED does **not** officially support the Pico W / RP2040 chip. Two separate feature requests for RP2040 support were formally closed by WLED maintainers as "not planned." WLED is built specifically for ESP8266/ESP32 (Espressif) chips.

**Decision:** Acquired the same ESP32 board used in the referenced video, specifically to run WLED for the LED matrix. Pico W remains idle/unused for now (available for future repurposing if needed).

### Updated Hardware Roles

| Component | Role |
|---|---|
| Windows Mini PC (NucBox5) | Central brain — OpenWeatherMap API calls, circadian phase calculation, sends commands via serial (to Mega) and MQTT/HTTP (to WLED on ESP32) |
| ESP32 (new) | Runs WLED firmware, drives the WS2812B 16x16 matrix, controlled via WLED's built-in JSON API / MQTT |
| Elegoo Mega 2560 | Drives the 2x SG90 servos (Sky Portal knob control) via USB serial from the mini PC — confirmed working (Leg 2 test) |
| Raspberry Pi Pico W | Currently idle — MQTT pipeline proven working, could be repurposed later if a wireless sensor or other node is ever added back |
| Mosquitto (on mini PC) | Broker kept running — reserved for future tablet control panel (final phase) and potentially for WLED's MQTT interface |

### Revised Data Flow

```
[Windows Mini PC — NucBox5]
    │ OpenWeatherMap API → circadian phase calculation
    │
    ├── USB Serial (pyserial) ──→ Elegoo Mega 2560 ──→ 2x SG90 servos ──→ Sky Portal knobs
    │
    └── MQTT / HTTP JSON API ──→ ESP32 (WLED) ──→ WS2812B 16x16 matrix
```

---

## Physical Build Status

- **3D printing in progress** for enclosure/mounting parts (following the design referenced in the WLED video) — estimated **~1 more day** until all parts are done
- **Known issue flagged:** trouble with the **back plate** during printing — not yet resolved/detailed; to be revisited if it recurs. Noting here so it isn't lost track of.

---

## Comprehensive Status Check — All Systems

| System | Status | Notes |
|---|---|---|
| Windows Mini PC networking | ✅ Done | Static IP `192.168.1.222`, gateway `192.168.1.254`, DNS `8.8.8.8`/`1.1.1.1`, Private network profile confirmed |
| Python environment | ✅ Done | Installed and working after installer/service hiccups |
| Mosquitto broker | ✅ Done | Listening on `0.0.0.0:1883` (fixed from localhost-only), firewall rule allowed, service confirmed running |
| VS Code + MicroPico | ✅ Done | Extension installed, Pico W firmware flashed, vREPL working |
| Arduino IDE + Mega 2560 | ✅ Done | Flashed, serial confirmed on COM3 |
| **Leg 1: Mosquitto loopback** | ✅ Confirmed | pub/sub tested locally |
| **Leg 2: Mega ↔ Python serial** | ✅ Confirmed | LED_ON test successful — this is the leg that matters going forward (servo control) |
| **Leg 3: Pico W → MQTT** | ✅ Confirmed | Full Wi-Fi → broker → subscriber chain validated (0–12 counter test) — pipeline proven, though Pico W's original job (sensor) is no longer part of the plan |
| BH1750 sensor | ❌ Not used | Architecture decision — using weather API instead |
| Circadian-phase Python script | ⬜ Not started | Next major software task |
| Mega servo control sketch | ⬜ Not started | Replace LED test sketch with real SG90 PWM code |
| ESP32 + WLED setup | ⬜ Not started | New hardware just acquired |
| Windows Scheduled Task | ⬜ Deferred | Waiting until control script exists |
| Tablet control panel | 🔜 Final phase | Explicitly deferred until core automation is finished; budget tablet options already researched (Fire HD 8, Galaxy Tab A8/A9, Lenovo Tab M10/M11) |

---

## To-Do List — Next Moves

### Immediate (while waiting on 3D prints, ~1 day)
1. [ ] Set up OpenWeatherMap API account/key if not already done
2. [ ] Flash WLED firmware onto the new ESP32 (via WLED's web installer or esptool)
3. [ ] Confirm ESP32 connects to Wi-Fi and WLED's web UI is reachable
4. [ ] Test WLED's JSON API / MQTT interface with simple manual commands (set color, brightness) before writing any control code
5. [ ] Revisit the back plate 3D print issue if it recurs — flag specifics (warping, layer separation, fitment, etc.) once seen again

### Once 3D prints are done
6. [ ] Physically mount ESP32 + WS2812B matrix using the printed enclosure
7. [ ] Mount SG90 servos onto Sky Portal knobs (Photon + Red/White Ratio)

### Core software build (can start in parallel with printing)
8. [ ] Write the circadian-phase Python script on the mini PC:
   - Pull solar elevation, cloud cover, UV index from OpenWeatherMap
   - Convert to photon level (0–100%) and color-temp ratio (0–100%)
9. [ ] Write the real Mega sketch: replace LED test code with SG90 servo PWM control, driven by serial commands from the Python script
10. [ ] Write the WLED control layer: Python script sends JSON API or MQTT commands to the ESP32 to update matrix color/brightness in sync with circadian phase
11. [ ] Integrate all three pieces into one continuous control loop on the mini PC
12. [ ] Set up the Windows Scheduled Task to run the finished script automatically at startup

### Final phase (explicitly deferred)
13. [ ] Tablet control panel — build a simple web dashboard (Flask or similar) for manual override, served from the mini PC, controlled via MQTT; select tablet hardware from previously researched options
