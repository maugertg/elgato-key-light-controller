"""
Filtering / Smoothing methods:
https://www.norwegiancreations.com/2015/10/tutorial-potentiometers-with-arduino-and-filtering/
https://electronics.stackexchange.com/questions/64677/how-to-smooth-potentiometer-values
https://en.wikipedia.org/wiki/Exponential_smoothing
https://www.programmingelectronics.com/tutorial-23-smoothing-data-old-version/
"""

import board
import displayio
import terminalio
import adafruit_displayio_ssd1306
from analogio import AnalogIn
from adafruit_display_text import label


pot_temp = AnalogIn(board.A2)  # 536 to 53401
pot_brightness = AnalogIn(board.A3)  # 536 to 53401

base = 50
low_value = 536
high_value = 53401
brightness_scaler = (high_value - low_value) / 100
temperature_scaler = (high_value - low_value) / 82

# Smoothing A Setup
ema_a = 0.5
ema_s = pot_brightness.value

# Smoothing B Setup
s = ema_s

scaled_s = int((pot_brightness.value / brightness_scaler) - 1)

while True:
    # Smoothing A Implementation
    sensor_value = pot_brightness.value
    ema_s = int((ema_a*sensor_value) + ((1-ema_a)*ema_s))
    
    # Smoothing B Implementation
    s += (sensor_value - s)/4
    # print((ema_s,int(s),pot_brightness.value,))

    # Smoothing A Implementation Scaled
    scaled_brightness = int((pot_brightness.value / brightness_scaler) - 1)
    scaled_s = int((ema_a*scaled_brightness) + ((1-ema_a)*scaled_s))

    scaled_temp = 50*(pot_temp.value / temperature_scaler)+2859
    stepped_temp = base * round(scaled_temp/base)

    print((scaled_brightness, int(scaled_s)))

    import time
    time.sleep(0.2)

