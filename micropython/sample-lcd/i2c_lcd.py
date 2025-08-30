# i2c_lcd.py - MicroPython用 I2C LCD ライブラリ
from lcd_api import LcdApi
from machine import I2C
import time

# PCF8574 のピン定義
MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
SHIFT_BACKLIGHT = 3
MASK_BACKLIGHT = (1 << SHIFT_BACKLIGHT)
SHIFT_DATA = 4

class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.backlight = MASK_BACKLIGHT
        self.busy_flag = 0
        time.sleep_ms(20)
        # 初期化シーケンス
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(1)
        self.hal_write_init_nibble(0x03)
        self.hal_write_init_nibble(0x02)
        super().__init__(num_lines, num_columns)

    def hal_backlight_on(self):
        self.backlight = MASK_BACKLIGHT
        self.hal_write_command(0)

    def hal_backlight_off(self):
        self.backlight = 0
        self.hal_write_command(0)

    def hal_write_command(self, cmd):
        self.hal_write_byte(cmd, 0)

    def hal_write_data(self, data):
        self.hal_write_byte(data, MASK_RS)

    def hal_write_init_nibble(self, nibble):
        byte = (nibble << SHIFT_DATA)
        self.hal_write_byte(byte, 0)

    def hal_write_byte(self, byte, mode):
        high = (byte & 0xF0) | mode | self.backlight
        low  = ((byte << 4) & 0xF0) | mode | self.backlight
        self.i2c.writeto(self.i2c_addr, bytes([high | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([high]))
        self.i2c.writeto(self.i2c_addr, bytes([low | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([low]))
