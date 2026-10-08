"""MAX30102 heart-rate demo for Raspberry Pi Pico.

Hardware connections and sensor setup follow project1_stpe2.py.
Requires max30102 driver, SpO2Calculators.py, st7789 and fonts.
For educational use only, not a medical device.
"""

from machine import SoftI2C, Pin, SPI
from time import sleep_ms, ticks_ms, ticks_diff
from neopixel import NeoPixel
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from max30102.circular_buffer import CircularBuffer
from SpO2Calculators import AcDcCalculator
import st7789
from font import vga1_16x32 as font1
from font import vga2_8x8 as font2

# Same ST7789 connections as the SpO2 demo
WIDTH, HEIGHT = 240, 240
BACKLIGHT_PIN = 20  # The original demo leaves backlight control unused
RST_PIN = 16
DC_PIN = 21
CS_PIN = 17
SCK_PIN = 18
MOSI_PIN = 19
SPI_NUM = 0

spi = SPI(SPI_NUM, baudrate=31250000,
          sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))
tft = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(RST_PIN, Pin.OUT),
    cs=Pin(CS_PIN, Pin.OUT),
    dc=Pin(DC_PIN, Pin.OUT),
    rotation=0
)
# Initialize ST7789 and turn on the display backlight (GP20).
# Both operations concern only the display; sensor configuration is unchanged.
backlight = Pin(BACKLIGHT_PIN, Pin.OUT)
backlight.value(1)  # Use 0 instead if your backlight is active-low.

SCREEN_BG = st7789.color565(255, 255, 255)
SCREEN_FG = st7789.color565(255, 0, 0)
tft.fill(SCREEN_BG)
tft.text(font1, "Heart Rate", 8, 8, SCREEN_FG)

# Same I2C and NeoPixel connections as the SpO2 demo
i2c = SoftI2C(sda=Pin(26), scl=Pin(27), freq=400000)
oximeter = MAX30102(i2c)
rgb_leds = NeoPixel(Pin(23), 4)


def set_leds(rgb):
    rgb_leds.fill(rgb)
    rgb_leds.write()


def display_reading(message, bpm, ir):
    # The screen is refreshed once per second by the existing main loop.
    # Use the same fill/text API and RGB565 colors as the working SpO2 demo.
    tft.fill(SCREEN_BG)
    tft.text(font1, "Heart Rate", 8, 8, SCREEN_FG)
    bpm_text = "BPM: --" if bpm is None else "BPM: {:.0f}".format(bpm)
    tft.text(font1, bpm_text, 8, 48, SCREEN_FG)
    tft.text(font2, str(message), 8, 104, SCREEN_FG)
    tft.text(font2, "IR: {}".format(ir), 8, 124, SCREEN_FG)


# Check the device before setting it up.
if oximeter.i2c_address not in i2c.scan():
    display_reading("Sensor not found", None, 0)
    set_leds((16, 0, 0))
    raise RuntimeError("MAX30102 not found on I2C")
if not oximeter.check_part_id():
    display_reading("Incorrect device ID", None, 0)
    set_leds((16, 0, 0))
    raise RuntimeError("I2C device is not MAX30102")

# Same acquisition settings as the SpO2 demo:
# 400 raw samples/s, averaged in groups of 8 -> 50 readings/s.
oximeter.setup_sensor()
oximeter.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
oximeter.set_sample_rate(400)
oximeter.set_fifo_average(8)
frequency = oximeter.get_acquisition_frequency()

# Reuse the SpO2 demo's IR peak/valley detector.
ir_calculator = AcDcCalculator(0.35)

# Each buffer element is the number of samples between two heartbeats.
beat_intervals = CircularBuffer(5)

FINGER_RED_THRESHOLD = 9000
FINGER_IR_THRESHOLD = 14000
CALIBRATION_SAMPLES = 100
MIN_BPM = 40
MAX_BPM = 180

samples_n = 0
previous_peak_index = None
finger_present = False
bpm = None
ir_reading = 0
last_display_ms = ticks_ms() - 1000

print("MAX30102 heart-rate monitor")
print("Effective sample frequency:", frequency, "Hz")
print("Place a finger on the sensor")

try:
    while True:
        # Read the sensor's FIFO and take one paired RED/IR sample.
        oximeter.check()
        if not oximeter.available():
            sleep_ms(2)
            continue

        red_reading = oximeter.pop_red_from_storage()
        ir_reading = oximeter.pop_ir_from_storage()

        # Same finger-detection thresholds as the original SpO2 demo.
        finger_now = (red_reading > FINGER_RED_THRESHOLD and
                      ir_reading > FINGER_IR_THRESHOLD)

        if not finger_now:
            if finger_present:
                # Finger removed: discard previous peaks and heart rate.
                ir_calculator.reset()
                beat_intervals.clear()
                samples_n = 0
                previous_peak_index = None
                bpm = None
            finger_present = False
        else:
            finger_present = True
            samples_n += 1

            # 1 means the detector has just confirmed a peak.
            result = ir_calculator.peak_valley_detection(
                ir_reading, samples_n)

            if result == 1:
                peak_index = ir_calculator.true_peak_index

                if previous_peak_index is not None and samples_n > CALIBRATION_SAMPLES:
                    interval = peak_index - previous_peak_index
                    if interval > 0:
                        current_bpm = 60.0 * frequency / interval

                        # Reject noise spikes / implausible heart rates.
                        if MIN_BPM <= current_bpm <= MAX_BPM:
                            beat_intervals.append(interval)
                            if len(beat_intervals) >= 3:
                                mean_interval = (sum(beat_intervals.data) /
                                                 len(beat_intervals))
                                bpm = 60.0 * frequency / mean_interval
                        else:
                            beat_intervals.clear()
                            bpm = None

                previous_peak_index = peak_index

                # The supplied calculator keeps these debug lists forever.
                # They are not needed to compute the peak-to-peak interval.
                if len(ir_calculator.peak_indexes) > 32:
                    ir_calculator.peak_indexes.clear()
                    ir_calculator.total_indexes.clear()

            # A missing pulse for 3 seconds invalidates the old measurement.
            if (previous_peak_index is not None and
                    samples_n - previous_peak_index > frequency * 3):
                ir_calculator.reset()
                beat_intervals.clear()
                previous_peak_index = None
                bpm = None

        # Limit screen, RGB and print updates to once per second.
        now = ticks_ms()
        if ticks_diff(now, last_display_ms) >= 1000:
            last_display_ms = now

            if not finger_present:
                status = "Place finger"
                set_leds((16, 0, 0))
            elif samples_n <= CALIBRATION_SAMPLES:
                status = "Calibrating"
                set_leds((16, 12, 0))
            elif bpm is None:
                status = "Measuring..."
                set_leds((16, 12, 0))
            else:
                status = "Signal detected"
                set_leds((0, 16, 0))

            display_reading(status, bpm, ir_reading)
            if bpm is None:
                print("{} | IR: {}".format(status, ir_reading))
            else:
                print("Heart rate: {:.1f} BPM | IR: {}".format(
                    bpm, ir_reading))

except KeyboardInterrupt:
    print("Measurement stopped")
finally:
    set_leds((0, 0, 0))
    oximeter.shutdown()


