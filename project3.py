from machine import Pin, ADC
import st7789
from st7789 import ST7789
from framebuf import FrameBuffer, RGB565
from time import sleep

muscle_sensor = ADC(26)

WIDTH, HEIGHT = 240, 240
BACKLIGHT_PIN = 20
RST_PIN = 16
DC_PIN = 21
CS_PIN = 17
SCK_PIN = 18  # SCK = SCL
MOSI_PIN = 19 # MOSI = SDA
SPI_NUM = 0

spi = machine.SPI(SPI_NUM, baudrate=31250000, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))
display = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(RST_PIN, Pin.OUT),
    cs=Pin(CS_PIN, Pin.OUT),
    dc=Pin(DC_PIN, Pin.OUT),
    backlight=Pin(BACKLIGHT_PIN, Pin.OUT),
    rotation=0,
)

display.fill(st7789.WHITE)
border_thickness = 5
bar_width = 25
bar_height = 200

#draw border for bar
display.fill_rect(20,15, border_thickness * 2 + bar_width, border_thickness * 2 + bar_height, st7789.BLACK)
smoothed_bar = 0  

while True:
    min_val = 65535
    max_val = 0
    
    # 1. Fast sampling window: Read 100 times continuously to capture the peaks and valleys of the EMG signal
    for _ in range(100):
        val = muscle_sensor.read_u16()
        if val < min_val: min_val = val
        if val > max_val: max_val = val
        # MicroPython loops are fast, no need for sleep here, let it sample at full speed
        
    # 2. Calculate amplitude (peak-to-peak): This represents the true AC strength of the muscle output
    amplitude = max_val - min_val
    
    # 3. Calculate percentage and limit the maximum value
    # Note: You may need to adjust 65536.0 here based on the maximum amplitude of your actual output (e.g., change to 30000.0)
    percentage = amplitude / 65536.0 
    if percentage > 1.0: 
        percentage = 1.0
        
    target_bar_amount = int(percentage * bar_height)
    
    # 4. Software smoothing filter (Exponential Moving Average - EMA)
    # 0.15 is the smoothing coefficient. Smaller value = smoother but delayed; Larger value = faster response but more jitter.
    smoothed_bar = smoothed_bar + 0.15 * (target_bar_amount - smoothed_bar)
    bar_amount = int(smoothed_bar)
    
    # 5. Screen drawing (kept original logic to minimize changes)
    # Optional optimization: Only redraw when the height changes to further reduce screen flickering
    display.fill_rect(20 + border_thickness, 15 + border_thickness, bar_width, (bar_height - bar_amount) , st7789.WHITE)
    display.fill_rect(20 + border_thickness, 15 + border_thickness + (bar_height - bar_amount), bar_width, bar_amount, st7789.RED)
