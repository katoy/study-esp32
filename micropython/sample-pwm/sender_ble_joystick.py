# receiver_ble_led_server.py  (BLE Peripheral: ESP32-Joystick)
# - MicroPython (ESP32) NimBLE + aioble
# - 128bit UUID / Notifyで X(2) Y(2) SW(1) を送信

import uasyncio as asyncio
import struct
import aioble
import bluetooth
from machine import Pin, ADC
from config import BLE_CONFIG  # BLE_CONFIG = {"name": "ESP32-Joystick"} を想定

# --- 128-bit UUID（送受で一致させる） ---
JOY_SVC_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
JOY_CHR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")

# --- ハード ---
joystick_x = ADC(Pin(34))  # 入力専用ピン
joystick_y = ADC(Pin(35))
joystick_btn = Pin(33, Pin.IN, Pin.PULL_UP)
joystick_x.atten(ADC.ATTN_11DB)
joystick_y.atten(ADC.ATTN_11DB)

# --- BLE サービス/キャラ ---
svc = aioble.Service(JOY_SVC_UUID)
ch_joy = aioble.Characteristic(svc, JOY_CHR_UUID, read=True, notify=True)
aioble.register_services(svc)

DEVICE_NAME = BLE_CONFIG.get("name", "ESP32-Joystick")

def read_payload() -> bytes:
    x = joystick_x.read()               # 0..4095
    y = joystick_y.read()
    sw = 0 if joystick_btn.value() == 0 else 1  # 押下=0, 非押下=1
    return struct.pack("<HHB", x, y, sw)

async def notify_loop(conn):
    while conn.is_connected():
        try:
            await ch_joy.notify(conn, read_payload())
        except Exception:
            # 未購読(CCCD OFF)や一時的なエラー時に少し待つ
            await asyncio.sleep_ms(100)
            continue
        await asyncio.sleep_ms(100)  # 10Hz

async def peripheral_task():
    while True:
        print("Advertising as:", DEVICE_NAME)
        # ★ このビルドでは advertise() が「接続を返す」
        conn = await aioble.advertise(
            interval_us=100_000,
            name=DEVICE_NAME,
            services=[JOY_SVC_UUID],
        )
        print("Connected:", conn.device)
        try:
            await notify_loop(conn)
        finally:
            await conn.disconnected()
            print("Disconnected")

asyncio.run(peripheral_task())
