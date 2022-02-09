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
    return response.json()['lights'][0]['on']

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
    pixel = setup_neopixel()
    switch = setup_button()

    pool = socketpool.SocketPool(wifi.radio)
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    use_neopixel(pixel, YELLOW)
    connect_to_wifi(pixel)

    # light_state = new_light_state = bool(get_light_state(session))
    light_state = new_light_state = False

    use_neopixel(pixel, BLUE)
    while True:
        # first pass: check real life
        switch.update()

        # second pass: assess state
        if switch.fell:
            light_state = bool(get_light_state(session))
            if light_state:
                new_light_state = False
            else:
                new_light_state = True

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


        light_state = new_light_state

if __name__ == '__main__':
    main()

