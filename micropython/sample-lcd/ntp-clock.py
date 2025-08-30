
# ntp-clock.py (lcd-test.pyスタイル)

from machine import Pin, I2C
from i2c_lcd import I2cLcd
import network
import ntptime
import time
import config

I2C_SCL = 22
I2C_SDA = 21
I2C_FREQ = 400_000
LCD_COLS = 16
LCD_ROWS = 2
I2C_ADDR = 0x27

i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=I2C_FREQ)
lcd = I2cLcd(i2c, I2C_ADDR, LCD_ROWS, LCD_COLS)

# WiFi接続表示
lcd.clear()
lcd.backlight_on()
lcd.putstr("Connecting WiFi\n")
# lcd.putstr("Please wait...  ")

lcd.clear()
lcd.putstr("WiFi Connected\n")
lcd.putstr("NTP Sync...   ")

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
time.sleep(1)  # 初期化直後に待機

# config.pyからSSIDとパスワード取得
ssid = config.AP_CONFIG.get('ssid', '')
password = config.AP_CONFIG.get('password', '')

try:
    sta_if.connect(ssid, password)
    retry = 0
    while not sta_if.isconnected():
        time.sleep(0.5)
        retry += 1
        if retry > 20:
            raise OSError("WiFi Connection Timeout")
    lcd.clear()
    lcd.putstr("WiFi Connected\n")
    lcd.putstr("NTP Sync...   ")
except OSError as e:
    lcd.clear()
    lcd.putstr("WiFi Error!   \n")
    lcd.putstr(str(e))
    time.sleep(3)
    raise

# NTPで時刻同期
try:
    ntptime.settime()
    lcd.clear()
    lcd.putstr("NTP Success!\n")
except Exception:
    lcd.clear()
    lcd.putstr("NTP Error!   \n")
    time.sleep(2)

def show_time():
    t = time.localtime(time.time() + 9*60*60)  # JST (UTC+9)
    lcd.move_to(0, 0)
    lcd.putstr("{:02d}:{:02d}:{:02d}      ".format(t[3], t[4], t[5]))
    lcd.move_to(0, 1)
    lcd.putstr("{:04d}-{:02d}-{:02d}   ".format(t[0], t[1], t[2]))

lcd.hide_cursor()  # カーソル消去
while True:
    show_time()
    time.sleep(1)
