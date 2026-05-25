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


while True:
    muscle_reading = muscle_sensor.read_u16()
    percentage = muscle_reading / 65536
    bar_amount = int((percentage * bar_height) * 1)
    #bar_amount = int(input("type num: "))
    sleep(0.05)
    print(bar_amount)
    #draw dead space
    display.fill_rect(20 + border_thickness, 15 + border_thickness, bar_width, (bar_height - bar_amount) , st7789.WHITE)
    display.fill_rect(20 + border_thickness, 15 + border_thickness + (bar_height - bar_amount), bar_width, bar_amount, st7789.RED)
   
    
