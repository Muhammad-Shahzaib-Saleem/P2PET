# relay.py
import RPi.GPIO as GPIO

RELAY_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)  # OFF (active LOW)

def relay_on():
    GPIO.output(RELAY_PIN, GPIO.LOW)

def relay_off():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
