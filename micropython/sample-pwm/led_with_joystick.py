from machine import Pin, PWM, ADC
import time

# GPIO 18, 19 を PWM 出力に設定
led1 = PWM(Pin(18), freq=1000)
led2 = PWM(Pin(19), freq=1000)

# ジョイスティックのX軸・Y軸をADCで取得（GPIO34, GPIO35）
joystick_x = ADC(Pin(34, Pin.IN))
joystick_y = ADC(Pin(35, Pin.IN))
# ADCの範囲を0〜4095に設定（ESP32の場合）
joystick_x.atten(ADC.ATTN_11DB)
joystick_y.atten(ADC.ATTN_11DB)

# ジョイスティックのプッシュボタン（GPIO33）
joystick_btn = Pin(33, Pin.IN, Pin.PULL_UP)

led_enabled = True  # LEDのON/OFF状態
last_btn_state = 1
last_toggle_time = 0
DEBOUNCE_MS = 50

def set_brightness(pwm, percent):
    duty = int(65535 * (percent / 100))
    pwm.duty_u16(duty)

while True:
    # ジョイスティックの値を取得
    x_val = joystick_x.read()
    y_val = joystick_y.read()
    # 0〜4095を0〜100に変換
    x_percent = int((x_val / 4095) * 100)
    y_percent = int((y_val / 4095) * 100)

    # プッシュボタンの状態取得
    btn_state = joystick_btn.value()
    now = time.ticks_ms()
    # ボタンが押された（LOW）かつチャタリング対策
    if btn_state == 0 and last_btn_state == 1:
        if (now - last_toggle_time) > DEBOUNCE_MS:
            led_enabled = not led_enabled
            print("Button pushed! LED toggled:", led_enabled)
            last_toggle_time = now
    last_btn_state = btn_state

    # LEDの明るさを設定（ON時のみ）
    if led_enabled:
        set_brightness(led1, x_percent)
        set_brightness(led2, y_percent)
    else:
        set_brightness(led1, 0)
        set_brightness(led2, 0)
    time.sleep(0.01)
