# sender.py
import time
from machine import Pin
from espnow_common import init_espnow, add_broadcast_peer, recv_bytes, BCAST, CHANNEL

# ESP-NOW 初期化（ブロードキャスト登録）
e, sta = init_espnow(channel=CHANNEL)
add_broadcast_peer(e, channel=CHANNEL)
print("Sender ready | ch:", sta.config('channel'), "| MAC:", sta.config('mac'))

# BOOT ボタン（押して離したら toggle 送信）
BUTTON_PIN = 0
btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

def send_cmd(cmd: bytes):
    cmd = bytes(cmd).strip()
    ok = e.send(BCAST, cmd, True)
    print(f"TX {cmd!r} ->", "OK" if ok else "FAIL")
    return ok

# ------ 起動時の状態同期 ------
time.sleep_ms(300)  # 起動直後の取りこぼし回避
led_state = None    # None=未同期, True/False=同期済み

for _ in range(3):
    send_cmd(b"ESP?")
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < 400:
        _, msg = recv_bytes(e, 50)
        if msg == b"STATE:ON":
            led_state = True
            print("SYNC(boot) -> LED ON")
            break
        elif msg == b"STATE:OFF":
            led_state = False
            print("SYNC(boot) -> LED OFF")
            break
        time.sleep_ms(5)
    if led_state is not None:
        break

if led_state is None:
    print("SYNC(boot) -> no reply (keep listening)")

# ------ メインループ ------
while True:
    # 押して離したら toggle を送信（簡易デバウンス）
    if not btn.value():                # 押下
        while not btn.value():         # 離すのを待つ
            time.sleep(0.01)
        send_cmd(b"toggle")
        time.sleep(0.2)                # チャタリング抑止

    # STATE 受信で led_state を同期（LED制御はしない）
    _, msg = recv_bytes(e, 20)
    if msg == b"STATE:ON":
        if led_state is not True:
            led_state = True
            print("SYNC -> LED ON")
    elif msg == b"STATE:OFF":
        if led_state is not False:
            led_state = False
            print("SYNC -> LED OFF")

    time.sleep(0.01)
