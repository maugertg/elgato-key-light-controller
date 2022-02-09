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

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

def connect_to_wifi():
    print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])
    print("Connecting to %s"%secrets["ssid"])
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("Connected to %s!"%secrets["ssid"])
    print("My IP address is", wifi.radio.ipv4_address)

def get_light_state(session):
    url = "http://192.168.1.159:9123/elgato/lights"


    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }

    response = session.get(url, headers=headers)
    print(response.json()['lights'][0]['on'])

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

def main():
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

    connect_to_wifi()

    pixel_pin = board.IO45
    num_pixels = 1
    pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.01, auto_write=False)

    pin = digitalio.DigitalInOut(board.IO5)
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    switch = Debouncer(pin)

    RED = (255, 0, 0)
    YELLOW = (255, 150, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (180, 0, 255)

    def use_neopixel(color):
        pixels.fill(color)
        pixels.show()

    led_state = switch.value

    while True:

        # first pass: check real life
        switch.update()
        # new_led_state = False

        # second pass: assess state
        if switch.fell:
            if led_state:
                new_led_state = False
            else:
                new_led_state = True
        else:
            new_led_state = led_state

        # third pass: reconcile state
        if led_state != new_led_state:
            if led_state:
                use_neopixel(GREEN)
                change_light_state(requests, 1)
            else:
                use_neopixel(RED)
                change_light_state(requests, 0)

        led_state = new_led_state

if __name__ == '__main__':
    main()

