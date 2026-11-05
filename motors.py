from machine import Pin, PWM
import time

# Assign PWM to the GPIO pins your ESCs will connect to
motor_front_left = PWM(Pin(16))
motor_front_right = PWM(Pin(17))
motor_back_left = PWM(Pin(18))
motor_back_right = PWM(Pin(19))

# Standard ESCs will be expecting a 50Hz frequency
motors = [motor_front_left, motor_front_right, motor_back_left, motor_back_right]
for m in motors:
    m.freq(50)

def set_throttle(motor, throttle_percent):
    """
    Converts a 0-100 throttle percentage to the correct MicroPython duty cycle.
    5% duty cycle (3276) = 1ms pulse (Motor OFF)
    10% duty cycle (6553) = 2ms pulse (Motor MAX SPEED)
    """
    # Clamp throttle between 0 and 100 for safety
    throttle = max(0, min(100, throttle_percent))
    
    min_duty = 3276
    max_duty = 6553
    
    duty = int(min_duty + (throttle / 100.0) * (max_duty - min_duty))
    motor.duty_u16(duty)

# ESCs require a 0% throttle signal for a few seconds to "arm" before they will spin
print("Arming ESCs... Please wait.")
for m in motors:
    set_throttle(m, 0)
time.sleep(3)
print("Motors armed and ready!")

# Example: Spin the front-left motor at 10% speed for 2 seconds
print("Spinning front-left motor...")
set_throttle(motor_front_left, 10)
time.sleep(2)
set_throttle(motor_front_left, 0)
print("Test complete.")