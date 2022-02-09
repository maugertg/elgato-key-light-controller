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

led_state = False

while True:
    # first pass: check real life
    switch.update()

    # second pass: assess state
    if switch.fell:
        if led_state:
            led_state = False
        else:
            led_state = True

    # third pass: reconcile state
    if led_state:
        use_neopixel(GREEN)
    else:
        use_neopixel(RED)