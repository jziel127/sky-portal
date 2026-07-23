import requests
import time
from datetime import datetime

try:
    from config import API_KEY, LAT, LON
except ImportError:
    print("WARNING: could not import config.py - using placeholder API key.")
    API_KEY = "YOUR_API_KEY_HERE"
    LAT, LON = 43.13, -88.22

WLED_IP = "192.168.1.209"
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

ORIENTATION = "rotate_ccw_then_flip_v"

# Palette
CLOCK_COLOR = (255, 140, 0)     # Warm Orange
BORDER_COLOR = (180, 80, 0)     # Muted Deep Amber (Harmonized)
DIVIDER_COLOR = (60, 60, 60)    # Soft Gray

TEMP_REFRESH_SECONDS = 15 * 60
VIEW_SWAP_SECONDS = 6
SLASH_BLINK_SECONDS = 0.6
ICON_ANIM_SECONDS = 0.4
MAIN_LOOP_TICK = 0.15

# ---------------- Fonts ----------------

# Standard 3x5 Font for Top Clock
DIGITS_5 = {
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
}

# Slim 2x5 Font for Bottom Date Display (Fits 4 digits + slash cleanly)
DIGITS_2x5 = {
    "0": ["11", "11", "11", "11", "11"],
    "1": ["10", "10", "10", "10", "10"],
    "2": ["11", "01", "11", "10", "11"],
    "3": ["11", "01", "11", "01", "11"],
    "4": ["11", "11", "11", "01", "01"],
    "5": ["11", "10", "11", "01", "11"],
    "6": ["11", "10", "11", "11", "11"],
    "7": ["11", "01", "01", "01", "01"],
    "8": ["11", "11", "11", "11", "11"],
    "9": ["11", "11", "11", "01", "11"],
}

SLASH_SLIM = ["01", "01", "10", "10", "10"]

# ---------------- Weather Icons ----------------

ICON_FRAMES = {
    "sun": [
        ["001100", "011110", "011110", "001100"],
        ["001100", "111111", "111111", "001100"],
    ],
    "cloud": [
        ["011100", "111111", "111111", "000000"],
        ["001110", "011111", "011111", "000000"],
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
    "cloud": (170, 170, 190),
    "rain": (60, 120, 220),
    "snow": (210, 240, 255),
}

CONDITION_TO_ICON = {
    "Clear": "sun", "Clouds": "cloud", "Rain": "rain", "Drizzle": "rain",
    "Thunderstorm": "rain", "Snow": "snow", "Mist": "cloud", "Fog": "cloud",
    "Haze": "cloud",
}

# ---------------- Drawing Helpers ----------------

def draw_bitmap(grid, rows, x_offset, y_offset, color):
    for row_idx, row in enumerate(rows):
        for col_idx, px in enumerate(row):
            if px == "1":
                x, y = x_offset + col_idx, y_offset + row_idx
                if 0 <= x < MATRIX_WIDTH and 0 <= y < MATRIX_HEIGHT:
                    grid[y][x] = color


def draw_border(grid, color):
    """Draws a 1-pixel outer border along matrix perimeter."""
    for x in range(MATRIX_WIDTH):
        grid[0][x] = color
        grid[MATRIX_HEIGHT - 1][x] = color
    for y in range(MATRIX_HEIGHT):
        grid[y][0] = color
        grid[y][MATRIX_WIDTH - 1] = color


# ---------------- Orientation Transform ----------------

def transform_coords(x, y, mode):
    n = MATRIX_WIDTH
    if mode == "none":
        return x, y
    if mode == "rotate_ccw_then_flip_v":
        xr, yr = y, n - 1 - x
        return xr, n - 1 - yr
    raise ValueError(f"Unknown orientation mode: {mode}")


# ---------------- Weather (Cached) ----------------

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
        icon = CONDITION_TO_ICON.get(condition, "cloud")
        _weather_cache.update(temp=temp, icon=icon, fetched_at=now)
        return temp, icon
    except Exception as e:
        print(f"  (weather fetch failed: {e}, using last known value)")
        return _weather_cache["temp"], _weather_cache["icon"]


# ---------------- Display Sections ----------------

def draw_clock(grid):
    now = datetime.now()
    hh, mm = now.strftime("%H"), now.strftime("%M")
    y_offset = 1
    draw_bitmap(grid, DIGITS_5[hh[0]], 1, y_offset, CLOCK_COLOR)
    draw_bitmap(grid, DIGITS_5[hh[1]], 4, y_offset, CLOCK_COLOR)
    draw_bitmap(grid, DIGITS_5[mm[0]], 9, y_offset, CLOCK_COLOR)
    draw_bitmap(grid, DIGITS_5[mm[1]], 12, y_offset, CLOCK_COLOR)


def draw_zigzag(grid):
    """2-row zigzag divider."""
    for x in range(1, 15):
        row = 7 if x % 2 == 0 else 8
        grid[row][x] = DIVIDER_COLOR


def draw_date_view(grid, slash_visible):
    """Uses compact 2x5 digits so MM/DD fits perfectly with comfortable margins."""
    now = datetime.now()
    month, day = now.strftime("%m"), now.strftime("%d")
    y_offset = 10
    x = 1

    # Month (2 digits, 2px wide each + 1px gap)
    draw_bitmap(grid, DIGITS_2x5[month[0]], x, y_offset, CLOCK_COLOR); x += 3
    draw_bitmap(grid, DIGITS_2x5[month[1]], x, y_offset, CLOCK_COLOR); x += 3

    # Blinking Slash
    if slash_visible:
        draw_bitmap(grid, SLASH_SLIM, x, y_offset, CLOCK_COLOR)
    x += 3

    # Day (2 digits, 2px wide each + 1px gap)
    draw_bitmap(grid, DIGITS_2x5[day[0]], x, y_offset, CLOCK_COLOR); x += 3
    draw_bitmap(grid, DIGITS_2x5[day[1]], x, y_offset, CLOCK_COLOR)


def draw_weather_view(grid, anim_frame_idx, session):
    temp, icon_name = get_weather(session)
    color = ICON_COLORS.get(icon_name, ICON_COLORS["cloud"])
    frames = ICON_FRAMES.get(icon_name, ICON_FRAMES["cloud"])
    frame = frames[anim_frame_idx % len(frames)]
    y_offset = 10

    draw_bitmap(grid, frame, 1, y_offset, color)
    temp_str = str(temp) if temp is not None else "--"
    
    # Draw temp digits
    x_start = 8
    for ch in temp_str:
        if ch in DIGITS_5:
            draw_bitmap(grid, DIGITS_5[ch], x_start, y_offset, color)
            x_start += 4


# ---------------- Sending Frames ----------------

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
    except requests.exceptions.RequestException as e:
        print(f"  (send to WLED failed: {e} - retrying...)")
        return None


def main():
    print("Starting Matrix Clock Loop with Border...")
    session = requests.Session()

    show_weather = False
    last_view_swap = time.time()
    last_slash_blink = time.time()
    slash_visible = True
    last_icon_tick = time.time()
    icon_frame_idx = 0

    while True:
        try:
            now = time.time()
            if now - last_view_swap > VIEW_SWAP_SECONDS:
                show_weather = not show_weather
                last_view_swap = now
            if now - last_slash_blink > SLASH_BLINK_SECONDS:
                slash_visible = not slash_visible
                last_slash_blink = now
            if now - last_icon_tick > ICON_ANIM_SECONDS:
                icon_frame_idx += 1
                last_icon_tick = now

            # Blank Grid
            grid = [[(0, 0, 0)] * MATRIX_WIDTH for _ in range(MATRIX_HEIGHT)]
            
            # Render Layers
            draw_border(grid, BORDER_COLOR)
            draw_clock(grid)
            draw_zigzag(grid)

            if show_weather:
                draw_weather_view(grid, icon_frame_idx, session)
            else:
                draw_date_view(grid, slash_visible)

            status = send_to_wled(grid, session)
            view = "WEATHER" if show_weather else "DATE"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] showing {view}, status={status}")

        except Exception as e:
            print(f"  (loop error: {e})")

        time.sleep(MAIN_LOOP_TICK)


if __name__ == "__main__":
    main()