"""
This file is an example for project2: Electrocardiograms
"""

from machine import Pin, ADC
import st7789
from st7789 import ST7789
from time import ticks_ms, ticks_diff
from framebuf import FrameBuffer, RGB565
#files for BPM text font and y axis voltage text font
from font import vga1_16x32 as main_font
from font import vga2_8x8 as voltage_font

#function to correct for wrong framebuffer color interpretation
def frame_buff_color565(r, g, b):
    val16 = (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3
    return (val16 >> 8) | ((val16 & 0xff) << 8)

bg_color = st7789.WHITE
border_color = st7789.BLACK
#set graph color to green
graph_color = frame_buff_color565(0,255,0)

heartbeat_threshold = 3.0
            # x , y
border_pos = (80, 20)
border_width = 150
border_height = 100
border_thickness = 5

debounce = False

ECG_sensor = ADC(26)
buzzer = Pin(1, Pin.OUT)

'''
spi = machine.SPI(0, baudrate = 40000000, polarity = 1, sck = Pin(18), mosi = Pin(19))
reset = Pin(16, Pin.OUT)
cs = Pin(17, Pin.OUT)
dc = Pin(21, Pin.OUT)

display = ST7789(spi, 240, 240, reset = reset, dc = dc, cs = cs)
'''

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

# display.init()
display.fill(st7789.WHITE)

#draw border for graph
display.fill_rect(border_pos[0], border_pos[1], border_width, border_height, border_color)

#draw voltage reference lines
#line 1
display.fill_rect(60, 25, 20, 4, border_color)
display.text(voltage_font, '3.3' + 'V', 25, 23, st7789.BLACK, bg_color)
#line 2
display.fill_rect(60, 42, 20, 4, border_color)
display.text(voltage_font, '2.64' + 'V', 25, 40, st7789.BLACK, bg_color)
#line 3
display.fill_rect(60, 59, 20, 4, border_color)
display.text(voltage_font, '1.98' + 'V', 25, 57, st7789.BLACK, bg_color)
#line 4
display.fill_rect(60, 76, 20, 4, border_color)
display.text(voltage_font, '1.32' + 'V', 25, 74, st7789.BLACK, bg_color)
#line 5
display.fill_rect(60, 93, 20, 4, border_color)
display.text(voltage_font, '0.66' + 'V', 25, 91, st7789.BLACK, bg_color)
#line 6
display.fill_rect(60, 110, 20, 4, border_color)
display.text(voltage_font, '0.0' + 'V', 25, 108, st7789.BLACK, bg_color)


#a list to track all times for when each heartbeat is detected
timestamps = []
#defines how many beats will be timed to calculate BPM
sample_size = 15


#subtract 10 (double of border_thickness) to account for border
graph_width = border_width - 10
graph_height = border_height - 10

#a buffer that contains all the pixels on our graph
buffer =  bytearray(graph_width * graph_height * 2)
#framebuffer used for displaying the graph
graph_fbuffer = FrameBuffer(buffer, graph_width, graph_height, RGB565)
#make all the pixels in the framebuffer white
graph_fbuffer.fill(bg_color)
#send framebuffer data to be displayed
display.blit_buffer(graph_fbuffer,
                    border_pos[0] + border_thickness,
                    border_pos[1] + border_thickness,
                    graph_width,
                    graph_height)


#15 points will be displayed on the graph at any given time
num_of_data_displayed = 15
#graph data will contain all the points to be plotted on the graph
graph_data = [50,50,50,50,50,50,50,50,50,50,50,50,50,50,50]
#the "x distance" between each point plotted on the graph
x_between_points = int(graph_width/(num_of_data_displayed - 1))
#scroll variable
cursor = 0

#displays "Average BPM: " texxt
display.text(main_font, "Average BPM: ", 30, 150, st7789.BLACK, bg_color)

while True:  
    # Reset framebuffer
    graph_fbuffer.fill(st7789.WHITE)
    
    # Draw the line graph... (keep your original drawing code unchanged here)
    for i in range(num_of_data_displayed - 1):
        graph_fbuffer.line(
                     x_between_points * i - cursor, 
                     graph_data[i],
                     x_between_points * (i + 1) - cursor,
                     graph_data[i + 1],
                     graph_color
                     )
        
    cursor = cursor + 5
    
    signal = ECG_sensor.read_u16()
    voltage = signal * 0.000050354
    
    if voltage > heartbeat_threshold and debounce == False:
        buzzer.value(1) # Heartbeat detected, turn on buzzer
        timestamps.append(ticks_ms())
        debounce = True                
            
        if len(timestamps) == sample_size:
            # 2. [Fix timing overflow & algorithm] Use ticks_diff to prevent overflow, and modify to use n-1 intervals
            time_for_sample_size = ticks_diff(timestamps[-1], timestamps[0])
            average_BPM = (sample_size - 1) / time_for_sample_size * 60000            
                        
            # 3. [Fix screen artifacting] Add two spaces after the string to overwrite any potentially remaining previous digits
            display.text(main_font, str(int(average_BPM)) + "  ", 30, 190, st7789.BLACK, bg_color)
                        
            timestamps.pop(0)         
        
    # 4. [Add hysteresis] Lower the reset threshold from 3.0V to 2.5V (or lower)
    elif voltage < 2.5 and debounce == True:
        buzzer.value(0) # Signal drops, turn off buzzer to create a complete "beep"
        debounce = False
    
    # Handle graph data scrolling... (keep your original logic unchanged here)
    if cursor >= x_between_points:
        cursor = 0
        graph_data.pop(0)        
        y_point = int(voltage / 3.3 * graph_height)
        graph_data.append(graph_height - y_point)
        
    # display framebuffer... (keep unchanged)
    display.blit_buffer(graph_fbuffer,
                    border_pos[0] + border_thickness,
                    border_pos[1] + border_thickness,
                    graph_width,
                    graph_height)
