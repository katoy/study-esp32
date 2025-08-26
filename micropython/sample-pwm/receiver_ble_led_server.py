# receiver_ble_led_server.py
# - ESP32 (MicroPython v1.26.0 aioble)
# - Peripheral 側 UUID:
#     SVC: 12345678-1234-5678-1234-56789abcdef0
#     CHR: 12345678-1234-5678-1234-56789abcdef1
# - 受信したジョイスティック X/Y を PWM duty に反映
# - ボタンは「押下の瞬間（1→0）」で LED の有効/無効をトグル（デバウンス付き）

import uasyncio as asyncio
import struct
import aioble
import bluetooth
import network, time
from machine import Pin, PWM
from config import AP_CONFIG, BLE_CONFIG

# === 設定 ===
DEVICE_NAME   = BLE_CONFIG.get("name", "ESP32-Joystick")
JOY_SVC_UUID  = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
JOY_CHR_UUID  = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")

# === LED(PWM) 初期化 ===
led1 = PWM(Pin(18), freq=1000)  # X
led2 = PWM(Pin(19), freq=1000)  # Y
led1.duty_u16(0)
led2.duty_u16(0)

# === トグル用の状態（押下=0, 非押下=1 前提） ===
enabled = True          # 現在のLED ON/OFF
last_sw = 1             # 直近のスイッチ状態
last_toggle_ms = 0      # 最後にトグルした時刻
last_x = 0              # 再開時に反映するための保持値
last_y = 0
DEBOUNCE_MS = 200       # デバウンス時間

# === Wi-Fi（必要な場合のみ） ===
sta = network.WLAN(network.STA_IF)
sta.active(True)
ssid = AP_CONFIG.get('ssid', '')
pwd  = AP_CONFIG.get('password', '')
if ssid:
    sta.connect(ssid, pwd)
    for _ in range(200):  # 最大 ~10秒待機
        if sta.isconnected():
            break
        time.sleep_ms(50)
    if sta.isconnected():
        print('Wi-Fi connected. IP address:', sta.ifconfig()[0])
    else:
        print('Wi-Fi connect timeout')
else:
    print('Wi-Fi skip (no SSID)')

# === ユーティリティ ===
def apply_pwm_from_xy(x_val: int, y_val: int):
    """0..4095 のADC値 → 0..65535 duty に拡大して反映"""
    duty_x = (x_val * 65535) // 4095
    duty_y = (y_val * 65535) // 4095
    led1.duty_u16(duty_x)
    led2.duty_u16(duty_y)

async def handle_notifications(ch):
    """CHRをNotify購読して、届いた5バイト(<HHB)を処理。押下エッジでトグル。"""
    global enabled, last_sw, last_toggle_ms, last_x, last_y
    await ch.subscribe(notify=True)
    print("Subscribed to notifications")

    while True:
        data = await ch.notified()   # Peripheral からの5バイト (<HHB)
        if not data or len(data) < 5:
            continue

        x_val, y_val, sw = struct.unpack("<HHB", data[:5])

        # エッジ検出（1→0 = 押下）＋デバウンス
        now = time.ticks_ms()
        if last_sw == 1 and sw == 0:
            if time.ticks_diff(now, last_toggle_ms) > DEBOUNCE_MS:
                enabled = not enabled
                last_toggle_ms = now
                if not enabled:
                    led1.duty_u16(0)
                    led2.duty_u16(0)
                else:
                    apply_pwm_from_xy(last_x, last_y)

        # 最終XYを保持（再開時に直ちに反映）
        last_x, last_y = x_val, y_val

        # 有効時のみPWM更新
        if enabled:
            apply_pwm_from_xy(x_val, y_val)

        # SW を最後に更新
        last_sw = sw

async def scan_and_connect():
    """スキャン→フィルタ（名前 or サービス）→接続→conn を返す"""
    print("Scanning for:", DEVICE_NAME)
    async with aioble.scan(duration_ms=5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            name = (result.name() or "")
            svcs = result.services() or ()
            if (DEVICE_NAME in name) or (JOY_SVC_UUID in svcs):
                print("Found:", name or "(no name)", result.device)
                try:
                    conn = await result.device.connect()
                    print("Connected")
                    return conn
                except Exception as e:
                    print("Connect failed:", e)
                    return None
    print("Device not found")
    return None

async def connect_once():
    """接続→サービス/キャラ取得→Notify購読→切断待ち"""
    conn = await scan_and_connect()
    if not conn:
        return False

    try:
        svc = await conn.service(JOY_SVC_UUID)
        ch  = await svc.characteristic(JOY_CHR_UUID)
    except Exception as e:
        print("Service/Char discovery failed:", e)
        try:
            await conn.disconnect()
        except:
            pass
        return False

    try:
        await handle_notifications(ch)
    except Exception as e:
        print("Notify loop err:", e)
    finally:
        try:
            await conn.disconnected()
        except:
            pass
        print("Disconnected")
    return True

async def ble_loop():
    """切断後に再スキャン・再接続を繰り返す"""
    while True:
        ok = await connect_once()
        await asyncio.sleep_ms(800 if ok else 1500)

async def main():
    await ble_loop()

asyncio.run(main())
