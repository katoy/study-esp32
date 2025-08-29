# --- モーター制御値生成（共通化） ---
def get_motor_param(motor_id, v):
    if v == 0:
        dir = 1
        speed = 0
    elif v > 0:
        dir = 1
        speed = min(abs(v), 255)
    else:
        dir = 2
        speed = min(abs(v), 255)
    return motor_id, dir, speed
import uasyncio as asyncio
# sender_toio_motor.py
# ESP32 + MicroPython + toio_controller_aioble.py
# ジョイスティックで toio の2モーターを制御。ボタンで全停止/再開。

import uasyncio as asyncio
from machine import Pin, ADC
from toio_controller_aioble import ToioControllerAioble

# --- ハード ---
joystick_x = ADC(Pin(34))
joystick_y = ADC(Pin(35))
joystick_btn = Pin(33, Pin.IN, Pin.PULL_UP)
joystick_x.atten(ADC.ATTN_11DB)
joystick_y.atten(ADC.ATTN_11DB)

# --- toio制御 ---
async def main():
    ctrl = ToioControllerAioble(debug=True)
    print("[toio] スキャン開始（toio本体は青点滅状態で！）")
    await ctrl.scan_and_connect(scan_ms=15000)
    await ctrl.discover_services()
    print("[toio] 接続・サービス取得完了。モーター制御開始")

    # キャリブレーション: 起動時の値を中央値とする
    center_x = joystick_x.read()
    center_y = joystick_y.read()
    print(f"[calib] center_x={center_x}, center_y={center_y}")

    enabled = True
    last_btn = joystick_btn.value()
    while True:
        x = joystick_x.read()  # 0..4095
        y = joystick_y.read()
        print(f"[joystick] x={x}, y={y}")
        btn = joystick_btn.value()
        # ボタンエッジで有効/停止トグル
        if last_btn == 1 and btn == 0:
            enabled = not enabled
            print(f"[toio] Motor {'ENABLED' if enabled else 'STOPPED'}")
        last_btn = btn
        # 中央判定（±200以内、キャリブレーション値基準）
        if abs(x-center_x)<300 and abs(y-center_y)<00 or not enabled:
            # ジョイスティック中央 or 停止時は完全停止
            l_id, l_dir, l_speed = 1, 1, 0
            r_id, r_dir, r_speed = 2, 1, 0
            pkt = bytes([0x01, l_id, l_dir, l_speed, r_id, r_dir, r_speed])
            print(f"[toio] Motor pkt: {list(pkt)} (STOP)")
            await ctrl.write_motor(pkt)
            await asyncio.sleep_ms(100)
            continue
        # X/Yを-255..255に変換（キャリブレーション値基準）
        v1 = int((x-center_x)/2048*255)
        v2 = int((y-center_y)/2048*255)
        print(f"[joystick] v1={v1}, v2={v2}")
    l_id, l_dir, l_speed = get_motor_param(1, v1)
    r_id, r_dir, r_speed = get_motor_param(2, v2)
    pkt = bytes([0x01, l_id, l_dir, l_speed, r_id, r_dir, r_speed])
    print(f"[toio] Motor pkt: {list(pkt)} (v1={v1}, v2={v2}, enabled={enabled})")
    await ctrl.write_motor(pkt)
    await asyncio.sleep_ms(100)

if __name__ == "__main__":
    asyncio.run(main())

