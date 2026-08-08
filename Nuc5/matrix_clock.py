"""
Sky Portal - LED Matrix Clock (v16 - Shifted Temp Alignment)
------------------------------------------------------------
- Shifted temperature reading 1px left (starting at col 8) for clean margins.
- Bottom Weather View: Animated Icon (Left) + Live Temperature (Right).
- Bottom Date View: Solid cycling slides (MONTH -> DATE -> DAY).
"""

import sys
import os

# Guarantee Nuc5 directory is in sys.path BEFORE importing config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import requests
import time
from datetime import datetime

try:
    from config import API_KEY, LAT, LON, WLED_IP
except ImportError:
    print("[MATRIX WARN] Could not import config.py - using fallbacks.")
    API_KEY = "YOUR_API_KEY_HERE"
    LAT, LON = 43.13, -88.22
    WLED_IP = "192.168.1.209"

MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
ORIENTATION = "rotate_ccw_then_flip_v"

# Palette
CLOCK_COLOR = (255, 140, 0)     # Warm Orange
BORDER_COLOR = (180, 80, 0)     # Warm Amber
DIVIDER_COLOR = (60, 60, 60)    # Soft Gray

TEMP_REFRESH_SECONDS = 15 * 60
VIEW_SWAP_SECONDS = 10          
MAIN_LOOP_TICK = 0.20

# ---------------- 3x5 Font Engine ----------------

FONT_3x5 = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "101", "101", "101"],
    "N": ["101", "111", "111", "101", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "P": ["111", "101", "111", "100", "100"],
    "Q": ["010", "101", "101", "110", "011"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "011"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "101", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "-": ["000", "000", "111", "000", "000"],
    " ": ["000", "000", "000", "000", "000"],
}

# --- Weather Bitmaps ---

MOON_BODY_BITMAP = [
    "001000",
    "010000",
    "011010",
    "001100"
]

CLOUD_BITMAP = [
    "000000",
    "001100",
    "011110",
    "000000"
]

ICON_FRAMES = {
    "sun": [
        ["001100", "011110", "011110", "001100"]
    ],
    "rain": [
        ["011100", "111111", "010010", "000000"],
        ["011100", "111111", "000000", "010010"],
    ],
    "snow": [
        ["010000", "000010", "001000", "100001"],
        ["000010", "010000", "100001", "001000"],
    ],
}

ICON_COLORS = {
    "sun": (255, 200, 0),
    "moon": (180, 220, 255),
    "cloud": (170, 170, 190),
    "rain": (60, 120, 220),
    "snow": (210, 240, 255),
}

STAR_COLOR_CYCLE = [
    (100, 240, 255),  # Cyan
    (180, 180, 255),  # Soft Violet
    (255, 220, 120),  # Warm Gold
    (255, 255, 255),  # Pure White
]

CONDITION_TO_ICON = {
    "Clear": "sun",
    "Clouds": "cloud",
    "Rain": "rain",
    "Drizzle": "rain",
    "Thunderstorm": "rain",
    "Snow": "snow",
    "Mist": "cloud",
    "Fog": "cloud",
    "Haze": "cloud",
}

# ---------------- Drawing Helpers ----------------

def draw_bitmap(grid, rows, x_offset, y_offset, color):
    for row_idx, row in enumerate(rows):
        for col_idx, px in enumerate(row):
            if px == "1":
                x, y = x_offset + col_idx, y_offset + row_idx
                if 1 <= x < (MATRIX_WIDTH - 1) and 0 <= y < MATRIX_HEIGHT:
                    grid[y][x] = color


def draw_pixel(grid, x, y, color):
    if 1 <= x < (MATRIX_WIDTH - 1) and 0 <= y < MATRIX_HEIGHT:
        grid[y][x] = color


def draw_border(grid, color):
    for x in range(MATRIX_WIDTH):
        grid[0][x] = color
        grid[MATRIX_HEIGHT - 1][x] = color
    for y in range(MATRIX_HEIGHT):
        grid[y][0] = color
        grid[y][MATRIX_WIDTH - 1] = color


def draw_centered_text(grid, text, y_offset, color):
    text = text.upper()
    total_px = (len(text) * 3) + (len(text) - 1)
    x_start = (MATRIX_WIDTH - total_px) // 2

    curr_x = x_start
    for ch in text:
        if ch in FONT_3x5:
            draw_bitmap(grid, FONT_3x5[ch], curr_x, y_offset, color)
        curr_x += 4


def transform_coords(x, y, mode):
    n = MATRIX_WIDTH
    if mode == "rotate_ccw_then_flip_v":
        xr, yr = y, n - 1 - x
        return xr, n - 1 - yr
    return x, y


# ---------------- Weather Cache ----------------

_weather_cache = {"temp": None, "icon": "cloud", "fetched_at": 0}


def get_weather(session):
    now = time.time()
    if _weather_cache["temp"] is not None and (now - _weather_cache["fetched_at"]) < TEMP_REFRESH_SECONDS:
        return _weather_cache["temp"], _weather_cache["icon"]
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial"
        )
        resp = session.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        temp = round(data["main"]["temp"])
        condition = data["weather"][0]["main"]

        hour = datetime.now().hour
        if condition == "Clear":
            icon = "sun" if (6 <= hour < 21) else "moon"
        else:
            icon = CONDITION_TO_ICON.get(condition, "cloud")

        _weather_cache.update(temp=temp, icon=icon, fetched_at=now)
        return temp, icon
    except Exception as e:
        print(f"[MATRIX WEATHER ERR] {e}")
        return _weather_cache["temp"], _weather_cache["icon"]


# ---------------- Display Rendering ----------------

def draw_clock(grid):
    now = datetime.now()
    hh, mm = now.strftime("%H"), now.strftime("%M")
    y_offset = 1
    draw_bitmap(grid, FONT_3x5[hh[0]], 1, y_offset, CLOCK_COLOR)
    draw_bitmap(grid, FONT_3x5[hh[1]], 4, y_offset, CLOCK_COLOR)
    draw_bitmap(grid, FONT_3x5[mm[0]], 9, y_offset, CLOCK_COLOR)
    draw_bitmap(grid, FONT_3x5[mm[1]], 12, y_offset, CLOCK_COLOR)


def draw_zigzag(grid):
    for x in range(1, 15):
        row = 7 if x % 2 == 0 else 8
        grid[row][x] = DIVIDER_COLOR


def draw_solid_date_view(grid, tick_counter):
    now = datetime.now()
    month_str = now.strftime("%b").upper()
    day_num = now.strftime("%d")
    day_name = now.strftime("%a").upper()

    slides = [month_str, day_num, day_name]
    slide_idx = (tick_counter // 6) % len(slides)

    draw_centered_text(grid, slides[slide_idx], 10, CLOCK_COLOR)


def draw_weather_view(grid, tick_counter, session):
    temp, icon_key = get_weather(session)
    y_offset = 10

    # 1. Draw Icon on Left (Cols 1-6)
    if icon_key == "moon":
        draw_bitmap(grid, MOON_BODY_BITMAP, 1, y_offset, ICON_COLORS["moon"])
        star_color = STAR_COLOR_CYCLE[(tick_counter // 2) % len(STAR_COLOR_CYCLE)]
        draw_pixel(grid, 1 + 5, y_offset + 0, star_color)

    elif icon_key == "cloud":
        jiggle_sequence = [0, 1, 0, -1]
        jiggle_offset = jiggle_sequence[(tick_counter // 3) % len(jiggle_sequence)]
        draw_bitmap(grid, CLOUD_BITMAP, 1 + jiggle_offset, y_offset, ICON_COLORS["cloud"])

    else:
        frames = ICON_FRAMES.get(icon_key, [CLOUD_BITMAP])
        bitmap = frames[tick_counter % len(frames)]
        color = ICON_COLORS.get(icon_key, ICON_COLORS["cloud"])
        draw_bitmap(grid, bitmap, 1, y_offset, color)

    # 2. Draw Temperature Reading on Right (Shifted 1px Left -> Starts at col 8)
    temp_str = str(temp) if temp is not None else "--"
    
    x_start = 8 if len(temp_str) == 2 else 7
    
    text_color = ICON_COLORS.get(icon_key, ICON_COLORS["cloud"])
    for ch in temp_str:
        if ch in FONT_3x5:
            draw_bitmap(grid, FONT_3x5[ch], x_start, y_offset, text_color)
            x_start += 4


# ---------------- WLED Transmission ----------------

def grid_to_wled_individual(grid):
    i_array = []
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            px, py = transform_coords(x, y, ORIENTATION)
            if py % 2 == 0:
                idx = py * MATRIX_WIDTH + px
            else:
                idx = py * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - px)
            r, g, b = grid[y][x]
            i_array.append(idx)
            i_array.append(f"{r:02X}{g:02X}{b:02X}")
    return i_array


def send_to_wled(grid, session):
    payload = {"seg": [{"id": 0, "i": grid_to_wled_individual(grid)}]}
    try:
        response = session.post(f"http://{WLED_IP}/json/state", json=payload, timeout=5)
        return response.status_code
    except requests.exceptions.RequestException:
        return None


def main():
    print("Starting Matrix Clock Loop (v16)...")
    session = requests.Session()

    show_weather = False
    last_view_swap = time.time()
    tick_counter = 0

    while True:
        try:
            now = time.time()
            if now - last_view_swap > VIEW_SWAP_SECONDS:
                show_weather = not show_weather
                last_view_swap = now

            tick_counter += 1

            grid = [[(0, 0, 0)] * MATRIX_WIDTH for _ in range(MATRIX_HEIGHT)]

            draw_border(grid, BORDER_COLOR)
            draw_clock(grid)
            draw_zigzag(grid)

            if show_weather:
                draw_weather_view(grid, tick_counter, session)
            else:
                draw_solid_date_view(grid, tick_counter)

            send_to_wled(grid, session)

        except Exception as e:
            print(f"  (matrix_clock error: {e})")

        time.sleep(MAIN_LOOP_TICK)


if __name__ == "__main__":
    main()