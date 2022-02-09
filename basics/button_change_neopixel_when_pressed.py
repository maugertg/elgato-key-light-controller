# SPDX-FileCopyrightText: 2019 Dave Astels for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=invalid-name

import time
import board
import digitalio
from adafruit_debouncer import Debouncer
import neopixel

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

while True:
    switch.update()
    if switch.fell:
        print("Just pressed")
    if switch.rose:
        print("Just released")
    if switch.value:
        print("not pressed")
        use_neopixel(RED)
    else:
        print("pressed")
        use_neopixel(GREEN)
    time.sleep(0.01)
