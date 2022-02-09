"""
From: https://learn.adafruit.com/debouncer-library-python-circuitpython-buttons-sensors/basic-debouncing
"""

# SPDX-FileCopyrightText: 2019 Dave Astels for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=invalid-name

import time
import board
import digitalio
from adafruit_debouncer import Debouncer

pin = digitalio.DigitalInOut(board.IO5)
pin.direction = digitalio.Direction.INPUT
pin.pull = digitalio.Pull.UP
switch = Debouncer(pin)

while True:
    switch.update()
    if switch.fell:
        print("Just pressed")
    if switch.rose:
        print("Just released")
    if switch.value:
        print("not pressed")
    else:
        print("pressed")
    time.sleep(0.1)
