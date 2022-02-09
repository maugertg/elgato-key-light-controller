"""
From:
https://learn.adafruit.com/monochrome-oled-breakouts/circuitpython-usage
https://learn.adafruit.com/circuitpython-display-support-using-displayio/text
"""

import board
import displayio
import terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label

# Release displays to avoid soft reset "Too many display busses" error
displayio.release_displays()

# Initialize I2C interface and display driver
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3d)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Create group to display context
main_group = displayio.Group()
display.show(main_group)

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
    x=5,
    y=14
)

splash.append(text_area_lables)

# Draw 2x scaled group for values
values = displayio.Group(scale=2)
main_group.append(values)

text_area_temp_val = label.Label(
    terminalio.FONT,
    # text="",
    color=0xFFFFFF,
    x=5,
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

while True:
    import time
    for i in range(1, 101):
        text_area_bright_val.text = f"{str(i)}%"
        text_area_temp_val.text = f"{str(2900+i*50)}"
        time.sleep(0.1)
    pass