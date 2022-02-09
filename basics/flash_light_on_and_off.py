"""
From: https://learn.adafruit.com/adafruit-metro-esp32-s2/circuitpython-internet-test
"""

import ipaddress
import ssl
import wifi
import socketpool
import json
import time
import adafruit_requests

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

    while True:
        time.sleep(2)
        change_light_state(requests, 1)
        time.sleep(2)
        change_light_state(requests, 0)

if __name__ == '__main__':
    main()
