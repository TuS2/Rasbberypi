import RPi.GPIO as GPIO
from time import sleep
GPIO.setwarnings(False)
# Direction pin from controller
DIR = 21
# Step pin from controller
STEP = 20
# 0/1 used to signify clockwise or counterclockwise.
CW = 1
CCW = 0,
DIR_1 = 7
STEP_1 = 1
GPIO.setmode(GPIO.BCM)

STEP_PULSE=31
STEP_DELAY=2110

# Establish Pins in software
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(DIR_1, GPIO.OUT)
GPIO.setup(STEP_1, GPIO.OUT)

try:
	# Run forever.

	"""Change Direction: Changing direction requires time to switch. The
	time is dictated by the stepper motor and controller. """
	# GPIO.output(DIR, 1)
	# GPIO.output(DIR_1, 1)
	# sleep(1)
	# for x in range(1125):
	# 	GPIO.output(STEP, 1)
	# 	GPIO.output(STEP_1, 1)
	# 	sleep(STEP_PULSE / 1000000)
	# 	GPIO.output(STEP, 0)
	# 	GPIO.output(STEP_1, 0)
	# 	sleep(STEP_DELAY / 1000000)

	sleep(1.0)
	GPIO.output(DIR, 1)
	GPIO.output(DIR_1, 0)
	for x in range(1120):
		GPIO.output(STEP, 1)
		GPIO.output(STEP_1, 1)
		sleep(STEP_PULSE / 1000000)
		GPIO.output(STEP, 0)
		GPIO.output(STEP_1, 0)
		sleep(STEP_DELAY / 1000000)

# Once finished clean everything up
except KeyboardInterrupt:
	print("cleanup")
	GPIO.output(STEP_1, GPIO.LOW)
	GPIO.output(STEP_1, GPIO.HIGH)
	GPIO.output(STEP, GPIO.LOW)
	GPIO.output(STEP, GPIO.HIGH)