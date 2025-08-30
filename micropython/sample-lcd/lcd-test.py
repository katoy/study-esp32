
# lcd-test.py (LCD1602A, I2C, MicroPython用)
from machine import Pin, I2C
from i2c_lcd import I2cLcd
import time

time.sleep_ms(500)  # LCD電源投入直後に待機

# LCD1602A I2C設定
I2C_SCL = 22
I2C_SDA = 21
I2C_FREQ = 40_000
LCD_COLS = 16
LCD_ROWS = 2
I2C_ADDR = 0x27   # I2Cスキャンで確認したアドレス

# I2C初期化
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=I2C_FREQ)

# LCD初期化
lcd = I2cLcd(i2c, I2C_ADDR, LCD_ROWS, LCD_COLS)
time.sleep_ms(1000)
lcd.backlight_on()
lcd.clear()
time.sleep_ms(500)

lcd.move_to(0, 0)
lcd.putstr("                ")  # 16文字に合わせてスペース追加
lcd.move_to(0, 1)
lcd.putstr("            ")  # 16文字に合わせてスペース追加

lcd.move_to(0, 0)
lcd.putstr("1602A I2C Test  ")  # 16文字に合わせてスペース追加
lcd.move_to(0, 1)
lcd.putstr("MicroPython OK  ")  # 16文字に合わせてスペース追加

lcd.hide_cursor()