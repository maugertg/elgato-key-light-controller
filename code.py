import ipaddress
import ssl
import wifi
import socketpool
import json
import time
import adafruit_requests

import board
import neopixel
import digitalio
from adafruit_debouncer import Debouncer

import displayio
import terminalio
import adafruit_displayio_ssd1306
from math import log
from analogio import AnalogIn
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_progressbar.horizontalprogressbar import HorizontalProgressBar

RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

def connect_to_wifi(pixel):
    print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])
    print("Connecting to %s"%secrets["ssid"], end="")
    use_neopixel(pixel, PURPLE)
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print(" - Connected!")
    print("My IP address is", wifi.radio.ipv4_address)

def get_light_state(session):
    print("Getting light state")
    url = "http://192.168.1.159:9123/elgato/lights"

    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }

    response = session.get(url, headers=headers)
    return response.json()['lights'][0]

def change_light_state(session, state):
    url = "http://192.168.1.159:9123/elgato/lights"

    payload = json.dumps({
      "lights": [
        {
          "on": state
        }
      ],
      "numberOfLights": 1
    })
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }

    response = session.put(url, headers=headers, data=payload)
    print(response.json()['lights'][0]['on'])

def change_light_brightness(session, brightness):
    url = "http://192.168.1.159:9123/elgato/lights"

    payload = json.dumps({
        "lights": [
            {
                "brightness": brightness
            }
        ],
        "numberOfLights": 1
    })
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }

    response = session.put(url, headers=headers, data=payload)
    print("brightness changed")
    # print(response.json()['lights'][0]['on'])

def change_light_temperature (session, temperature):
    url = "http://192.168.1.159:9123/elgato/lights"

    payload = json.dumps({
        "lights": [
            {
                "temperature": temperature
            }
        ],
        "numberOfLights": 1
    })
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }

    response = session.put(url, headers=headers, data=payload)
    print("temperature changed")
    # print(response.json()['lights'][0]['on'])

def setup_neopixel():
    pixel_pin = board.IO45
    num_pixels = 1
    return neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.01, auto_write=False)

def setup_button():
    pin = digitalio.DigitalInOut(board.IO5)
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    return Debouncer(pin)

def use_neopixel(pixel, color):
    pixel.fill(color)
    pixel.show()


def initialize_i2c_display():
    # Initialize I2C interface and display driver
    i2c = board.I2C()
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3d)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)
    return display

def create_boarder_display_context():
    # Make the display context for boarder
    splash = displayio.Group()

    WIDTH = 128
    HEIGHT = 64  # Change to 64 if needed
    BORDER = 1

    # Draw full screen rectangle
    color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000  # Black
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
    splash.append(inner_sprite)

    return splash

def create_text_labels(x_pos, y_pos, text=""):
    return label.Label(
        terminalio.FONT,
        text=text,
        color=0xFFFFFF,
        x=x_pos,
        y=y_pos
    )

def knob_state_delta_more_than_one(new_state, old_state, threshold=0.95):
    return bool(old_state-threshold > new_state or new_state > old_state+threshold)

def main():
    # Release and initialize displays to avoid soft reset "Too many display busses" error
    displayio.release_displays()
    display = initialize_i2c_display()

    # Setup the display groups and contexts
    main_group = displayio.Group()

    # Create primary display group with boarder
    splash = create_boarder_display_context()
    # main_group.append(splash)

    # Create a new progress_bar objects at their x, y locations
    progress_bar_width = 104
    progress_bar_height = 5
    process_bar_x = 12

    progress_bar_temp = HorizontalProgressBar((process_bar_x, 5), (progress_bar_width, progress_bar_height), 0, 100, border_thickness=0)
    progress_bar_bright = HorizontalProgressBar((process_bar_x, 55), (progress_bar_width, progress_bar_height), 0, 100, border_thickness=0)

    # Append progress_bars to the splash group
    main_group.append(progress_bar_bright)    
    main_group.append(progress_bar_temp)    

    # Creat labels for pot values 
    main_group.append(create_text_labels(x_pos=7, y_pos=20, text="Temp:      Power:"))

    # Create group for pot values at 2x scale
    values = displayio.Group(scale=2)
    main_group.append(values)

    # Create Color Temperature text lable
    value_y_pos = 19

    text_area_temp_val = create_text_labels(x_pos=4, y_pos=value_y_pos)
    values.append(text_area_temp_val)

    # Create Brightness text label
    text_area_bright_val = create_text_labels(x_pos=37, y_pos=value_y_pos)
    values.append(text_area_bright_val)

    # Setup potentiometers
    pot_temp = AnalogIn(board.A2)  # outputs values from 536 to 53401
    pot_brightness = AnalogIn(board.A3)  # outputs values from 536 to 53401

    # Values used to scale pot output
    base = 50
    low_value = 536
    high_value = 53401

    # Chunk pot output into appropriate number of values based on API input
    brightness_scaler = (high_value - low_value) / 100
    temperature_api_scaler = (high_value - low_value) / 100

    # Setup neopixel and switch input
    pixel = setup_neopixel()
    switch = setup_button()

    # Connect to WiFi
    use_neopixel(pixel, YELLOW)
    connect_to_wifi(pixel)

    # Refresh Display
    display.show(main_group)

    # Setup HTTP session handler
    pool = socketpool.SocketPool(wifi.radio)
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    # Query light for current state values:
    starting_light_state = get_light_state(session)

    # Setup initial light state values
    light_state = new_light_state = False
    adjust_brightness = False
    brightness_state = starting_light_state.get("brightness")
    brightness_changes = 0
    adjust_temperature = False
    temperature_state = starting_light_state.get("temperature")
    temperature_changes = 0

    # Update neopixel to indicate WiFi has connected and the code has entered the primary loop
    use_neopixel(pixel, BLUE)

    while True:
        ### first pass: check real life
        switch.update()
        
        # Scale the brightness pot output between 0 and 100
        scaled_brightness = (pot_brightness.value / brightness_scaler) - 1

        # Pot value used for API interactions
        scaled_temp_api = (pot_temp.value / temperature_api_scaler) - 1
        scaled_temp_api_value = (scaled_temp_api * 2) + 143

        # Logarithmically Scale the temp api value between 2900 and 7000
        # scaled_temp_display = -5000*log(2*(scaled_temp_api_value-107.11591),10)+16280
        scaled_temp_display = -1667*log(2*(scaled_temp_api_value-99),2)+17770

        # Adjust the temp display value by steps of 50
        stepped_temp_display = base * round(scaled_temp_display/base)

        ### second pass: assess state
        if switch.rose:
            light_state = bool(get_light_state(session)['on'])
            if light_state:
                new_light_state = False
            else:
                new_light_state = True

        if scaled_brightness != brightness_state and knob_state_delta_more_than_one(scaled_brightness, brightness_state):
            adjust_brightness = True

        if scaled_temp_api_value != temperature_state and knob_state_delta_more_than_one(scaled_temp_api_value, temperature_state, threshold=1.5):
            adjust_temperature = True

        ### third pass: reconcile state
        if light_state != new_light_state:
            if light_state:
                use_neopixel(pixel, RED)
                print("Turning light off")
                change_light_state(session, 0)
            else:
                use_neopixel(pixel, GREEN)
                print("Turning light on")
                change_light_state(session, 1)

        if adjust_brightness:
            change_light_brightness(session, scaled_brightness)
            brightness_changes += 1
            print(brightness_changes)
            brightness_state = scaled_brightness
            adjust_brightness = False

        if adjust_temperature:
            change_light_temperature(session, scaled_temp_api_value)
            temperature_changes += 1
            print(temperature_changes)
            temperature_state = scaled_temp_api_value
            adjust_temperature = False
        
        text_area_temp_val.text = f"{str(stepped_temp_display)}"
        progress_bar_temp.value = int(scaled_temp_api)
        
        text_area_bright_val.text = f"{str(int(scaled_brightness))}%"
        progress_bar_bright.value = int(scaled_brightness)


        light_state = new_light_state

if __name__ == '__main__':
    main()
