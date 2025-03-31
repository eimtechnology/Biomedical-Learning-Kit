#import Pin and SoftI2C class for communication
from machine import SoftI2C, Pin, SPI
#import class to control pulse oximeter, import constant for light level
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from time import sleep
#import AcDcCalculator class and calculate_SpO2 function
from SpO2Calculators import AcDcCalculator
#impor NeoPixel class for RGB LEDs
from neopixel import NeoPixel
#from system import exit

#set adaptive threshold value to 35%
red_calculator = AcDcCalculator(0.35)
ir_calculator = AcDcCalculator(0.35) 

#I2C object for pulse oximeter object, make sure sda and scl pins match your wiring
i2c = SoftI2C(sda = Pin(26), scl = Pin(27), freq = 400000)

#pulse oximeter object to communicate with sensor
oximeter = MAX30102(i2c)

rgb_leds = NeoPixel(Pin(23), 4)

#scan for sensor and connect if found
if oximeter.i2c_address not in i2c.scan():
    print("Sensor not found.")
    exit()
elif not oximeter.check_part_id():
    print("I2C device ID not corresponding to MAX30102")
    exit()
else:
    print("Sensor found, connecting")
    
#set up sensor with default settings
oximeter.setup_sensor()

#change light level setting to "medium"
oximeter.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)

#set frequency at which samples are take (400 times/second)
oximeter.set_sample_rate(400)

# Set the number of samples to be averaged per each reading
oximeter.set_fifo_average(8)

#variable to track samples read
samples_n = 0
#variable to track SpO2 percentage
SpO2 = 91
while True:
    #gather data from sensor's internal FIFO memory queue
    oximeter.check()
    
    #if the gathered data contains samples
    if oximeter.available():        
        
        #take 1 red and ir light sample from the data gathered
        red_reading = oximeter.pop_red_from_storage()
        ir_reading = oximeter.pop_ir_from_storage()    
        
        #increment counter by 1 since we read a new sample
        samples_n = samples_n + 1
        
        #if a finger is on the sensor
        if red_reading > 9000 and ir_reading > 14000:
            #find peaks and valleys in ir and red PPG waves
            red_result = red_calculator.peak_valley_detection(red_reading, samples_n)                
            ir_calculator.peak_valley_detection(ir_reading, samples_n)
                
            #start calculating SpO2 after 100 samples, this is done to calibrate thresholds
            if samples_n > 100:
                #calculate AC/DC ratios 
                ir_ratio = ir_calculator.calculate_ratio()
                red_ratio = red_calculator.calculate_ratio()
                
                #if the ratios calculate a valid result
                if ir_ratio != None and red_ratio != None:
                    #print and calculate SpO2 using AC/DC ratios
                    SpO2 = 104 - 17 * (red_ratio / ir_ratio)
                    print("SpO2 calculation: ", SpO2)
            
            else:
                print("Calibrating")
        else:
            #reset calculators and sample number
            samples_n = 0
            red_calculator.reset()
            ir_calculator.reset()
            #wait 5 seconds for sensor to read finger so that if there's a finger is on the next reading, it had enough time to settle
            print('Delay')
            sleep(5)
     
    if SpO2 < 90:
        rgb_leds.fill((16,0,0))
    elif SpO2 > 90 and SpO2 < 95:
        rgb_leds.fill((16,12,0))
    elif SpO2 > 95:
        rgb_leds.fill((0,16,0))
    rgb_leds.write()