import ipaddress
import ssl
import wifi
import socketpool
import json
import time
import adafruit_requests

import board
import digitalio
from adafruit_debouncer import Debouncer
import neopixel


import displayio
import terminalio
import adafruit_displayio_ssd1306
from analogio import AnalogIn
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

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

def main():
    # Release displays to avoid soft reset "Too many display busses" error
    displayio.release_displays()

    # Initialize I2C interface and display driver
    i2c = board.I2C()
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3d)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

    # Create group to display context
    main_group = displayio.Group()
    # display.show(main_group)

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

    main_group.append(splash)

    # Draw value labels
    text_area_lables = label.Label(
        terminalio.FONT,
        text="Temp:      Power:",
        color=0xFFFFFF,
        x=7,
        y=14
    )

    splash.append(text_area_lables)

    # Draw 2x scaled group for values
    helvetica = bitmap_font.load_font("fonts/Helvetica-Bold-16.bdf")

    values = displayio.Group(scale=2)
    main_group.append(values)

    text_area_temp_val = label.Label(
        terminalio.FONT,
        # helvetica,
        # text="",
        color=0xFFFFFF,
        x=4,
        y=15
    )
    values.append(text_area_temp_val)

    text_area_bright_val = label.Label(
        terminalio.FONT,
        # text="",
        color=0xFFFFFF,
        x=37,
        y=15
    )
    values.append(text_area_bright_val)

    # Setup potentiometers
    pot_temp = AnalogIn(board.A2)  # 536 to 53401
    pot_brightness = AnalogIn(board.A3)  # 536 to 53401

    base = 50
    low_value = 536
    high_value = 53401
    brightness_scaler = (high_value - low_value) / 100
    temperature_scaler = (high_value - low_value) / 82

    pixel = setup_neopixel()
    switch = setup_button()

    pool = socketpool.SocketPool(wifi.radio)
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    use_neopixel(pixel, YELLOW)
    connect_to_wifi(pixel)


    display.show(main_group)

    starting_light_state = get_light_state(session)
    light_state = new_light_state = False
    adjust_brightness = False
    brightness_state = starting_light_state.get("brightness")

    use_neopixel(pixel, BLUE)
    while True:
        # first pass: check real life
        switch.update()

        scaled_brightness = int((pot_brightness.value / brightness_scaler) - 1)
        scaled_temp = 50*(pot_temp.value / temperature_scaler)+2859
        stepped_temp = base * round(scaled_temp/base)


        # second pass: assess state
        if switch.rose:
            light_state = bool(get_light_state(session)['on'])
            if light_state:
                new_light_state = False
            else:
                new_light_state = True

        if scaled_brightness != brightness_state:
            adjust_brightness = True

        # third pass: reconcile state
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
            brightness_state = scaled_brightness
            adjust_brightness = False


        text_area_bright_val.text = f"{str(scaled_brightness)}%"
        text_area_temp_val.text = f"{str(stepped_temp)}"


        light_state = new_light_state
        

        # time.sleep(0.2)

if __name__ == '__main__':
    main()

