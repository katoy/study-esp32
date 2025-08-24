from machine import Pin, PWM
import time

# GPIO 18, 19 を PWM 出力に設定
led1 = PWM(Pin(18), freq=1000)
led2 = PWM(Pin(19), freq=1000)

def set_brightness(pwm, percent):
    duty = int(65535 * (percent / 100))
    pwm.duty_u16(duty)

while True:
    for p in range(0, 101, 5):
        set_brightness(led1, p)
        set_brightness(led2, 100 - p)
        time.sleep(0.05)
