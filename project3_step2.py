from machine import Pin, ADC
import st7789
from st7789 import ST7789
from framebuf import FrameBuffer, RGB565
from time import sleep

muscle_sensor = ADC(26)

spi = machine.SPI(0, baudrate = 40000000, polarity = 1, sck = Pin(18), mosi = Pin(19))
reset = Pin(16, Pin.OUT)
cs = Pin(17, Pin.OUT)
dc = Pin(21, Pin.OUT)


display = ST7789(spi, 240, 240, reset = reset, dc = dc, cs = cs)

display.fill(st7789.WHITE)
border_thickness = 5
bar_width = 25
bar_height = 200

#draw border for bar
display.fill_rect(20,15, border_thickness * 2 + bar_width, border_thickness * 2 + bar_height, st7789.BLACK)


while True:
    muscle_reading = muscle_sensor.read_u16()
    percentage = muscle_reading / 65536
    bar_amount = int((percentage * bar_height) * 3.5)
    #bar_amount = int(input("type num: "))
    sleep(0.05)
    print(bar_amount)
    #draw dead space
    display.fill_rect(20 + border_thickness, 15 + border_thickness, bar_width, (bar_height - bar_amount) , st7789.WHITE)
    display.fill_rect(20 + border_thickness, 15 + border_thickness + (bar_height - bar_amount), bar_width, bar_amount, st7789.RED)
   
    