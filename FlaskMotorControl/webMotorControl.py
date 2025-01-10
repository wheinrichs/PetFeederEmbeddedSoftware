from pymongo import MongoClient
import time
from datetime import datetime
import RPi.GPIO as gpio
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = "66fc7556e4c49981b7d47681"
MONGO_CLIENT = os.getenv("MONGO_CLIENT")


client = MongoClient(MONGO_CLIENT)
db=client["test"]

schedule_collection = db["schedule"]

# Set gpio warnings to false
gpio.setwarnings(False)

# Declare the pins for the board
direction_pin = 20
pulse_pin = 21
cw_direction = 0
ccw_direction = 1

# Declare the pins as output
gpio.setmode(gpio.BCM)
gpio.setup(direction_pin, gpio.OUT)
gpio.setup(pulse_pin, gpio.OUT)
gpio.output(direction_pin, cw_direction)

# Steps per revolution with half stepping
stepsPerRevolution = 200 * 2

# Inputs
timeForOneRotation = 8
timeDelayPerStep = timeForOneRotation/stepsPerRevolution

def get_preferences():
    # Flag to say found schedule
    global foundUserSchedule
    preferences = schedule_collection.find_one({"user_id": ACCOUNT_ID})
    if preferences:
        foundUserSchedule = True
        global schedule
        schedule = preferences.get("schedule", [])
        global portion
        portion = preferences.get("portion", [])
        return
    else:
        foundUserSchedule = False
        print("No portion or schedule")

def check_and_move_motor():
    global current_time
    global current_date
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime('%Y-%m-%d')
    day_of_week = get_day_of_week(current_date)
    get_preferences()
    if foundUserSchedule:
        if current_time in schedule[day_of_week]:
            move_motor()  # Implement motor movement logic here
            time.sleep(60)  # Prevent multiple triggers within the same minute

def get_day_of_week(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    day_index = date_obj.weekday()
    days_of_week = ['M', 'T', 'W', 'Th', 'F', 'S', 'Su']
    return days_of_week[day_index]

def move_motor():
    print("Moving motor to dispense ", portion, " portions at ", current_time, " on ", current_date)
    # Each portion is 1/6 cups, but the pockets hold about 1/12 of a cup so need 2
    rotationDegrees = portion * 2 * 36

    # Calculate the distinct steps needed
    steps_needed = int(rotationDegrees * stepsPerRevolution / 360)

    print(f"Rotation degrees: {rotationDegrees}, Steps needed: {steps_needed}")

    for x in range(steps_needed):
        gpio.output(pulse_pin, gpio.HIGH)
        time.sleep(timeDelayPerStep / 2)
        gpio.output(pulse_pin, gpio.LOW)
        time.sleep(timeDelayPerStep / 2)

if __name__ == "__main__":
    while True:
        check_and_move_motor()
        time.sleep(30)  # Check the schedule every 30 seconds