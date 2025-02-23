import time
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import Adafruit_ADS1x15

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setwarnings(False)

# Define pins for the traffic light LEDs
RED_PIN = 17
YELLOW_PIN = 27
GREEN_PIN = 22

# Setup the traffic light GPIO pins as outputs
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)

# Setup the ADC (ADS1115)
adc = Adafruit_ADS1x15.ADS1115()
GAIN = 1  # Gain for the ADC
AMBULANCE_THRESHOLD = 6500  # Threshold for detecting an ambulance

# Setup the LCD (16x2) display
lcd = CharLCD('PCF8574', 0x27)  # LCD address is typically 0x27 or 0x3F

# Function to read from the ADC (e.g., reading an analog sensor)
def read_adc(channel=0):
    try:
        value = adc.read_adc(channel, gain=GAIN)
        print(f"ADC Value (Channel {channel}): {value}")
        return value
    except Exception as e:
        print(f"Error reading ADC: {e}")
        return 0

# Function to display traffic signal status on LCD
def display_signal_status(status):
    lcd.clear()
    lcd.write_string(status)
    time.sleep(1)

# Function to activate the green signal for emergency mode
def emergency_mode():
    print("Activating Emergency Mode...")
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.HIGH)  # Turn on green for ambulance
    display_signal_status("EMERGENCY: GREEN")
    time.sleep(10)  # Keep the green light for 10 seconds
    GPIO.output(GREEN_PIN, GPIO.LOW)  # Reset green light after emergency

# Function to control the normal traffic signal
def manual_traffic_signal():
    print("Normal Signal Mode: Red -> Yellow -> Green")

    # Red light ON
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    for _ in range(20):  # Check for emergency every 1 second during 20-second delay
        if read_adc(channel=0) >= AMBULANCE_THRESHOLD:
            emergency_mode()
            return
        display_signal_status("RED: STOP")
        time.sleep(1)

    # Yellow light ON
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    for _ in range(5):  # Check for emergency every 1 second during 5-second delay
        if read_adc(channel=0) >= AMBULANCE_THRESHOLD:
            emergency_mode()
            return
        display_signal_status("YELLOW: SLOW")
        time.sleep(1)

    # Green light ON
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    for _ in range(20):  # Check for emergency every 1 second during 20-second delay
        if read_adc(channel=0) >= AMBULANCE_THRESHOLD:
            emergency_mode()
            return
        display_signal_status("GREEN: GO")
        time.sleep(1)

    # Reset the green light
    GPIO.output(GREEN_PIN, GPIO.LOW)

# Main program loop
try:
    print("Starting traffic light control system...")
    while True:
        # Read the analog sensor value (from channel 0)
        sensor_value = read_adc(channel=0)

        # Check for emergency condition
        if sensor_value >= AMBULANCE_THRESHOLD:  # Detect ambulance
            print(f"Ambulance detected! Sensor Value: {sensor_value}")
            emergency_mode()  # Switch to emergency mode immediately
        else:
            # If no ambulance detected, proceed with normal traffic signal
            manual_traffic_signal()

except KeyboardInterrupt:
    # Cleanup GPIO and LCD before exiting
    GPIO.cleanup()
    lcd.clear()
    lcd.write_string("Exiting...")
    print("Program exited cleanly.")
