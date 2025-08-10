# sender.py  — BC運用 / LED制御なし / 起動時同期あり
import time
from machine import Pin
from espnow_utils import init_espnow, add_peer_with_channel

CHANNEL = 1
BCAST   = b'\xff\xff\xff\xff\xff\xff'

# ESP-NOW 初期化（チャネル固定・省電力OFFは espnow_utils 側）
e, sta = init_espnow(channel=CHANNEL)
add_peer_with_channel(e, BCAST, channel=CHANNEL)

# BOOTボタン（押して離したら toggle 送信）
BUTTON_PIN = 0
boot_button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# 受け取ったリモートLED状態（表示用の変数だけ保持）
led_state = None  # None=未同期, True=ON, False=OFF

def send_cmd(cmd: bytes):
    cmd = bytes(cmd).strip()
    ok = e.send(BCAST, cmd, True)
    print(f"TX {cmd!r} ->", "OK" if ok else "FAIL")
    return ok

print("Sender ready | ch:", sta.config('channel'), "| MAC:", sta.config('mac'))

# ===== 起動時の状態同期 =====
# "ESP?" を数回ブロードキャスト → receiver が STATE:ON/OFF を返す想定
for i in range(3):
    send_cmd(b"ESP?")
    # 返答待ち（短めループ）
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < 300:
        host, msg = e.recv(50)
        if msg:
            try:
                bmsg = bytes(msg).strip()
            except Exception:
                bmsg = msg.tobytes().strip() if hasattr(msg, "tobytes") else msg
            if bmsg == b"STATE:ON":
                led_state = True
                print("SYNC(boot) -> LED ON")
                break
            elif bmsg == b"STATE:OFF":
                led_state = False
                print("SYNC(boot) -> LED OFF")
                break
        time.sleep_ms(5)
    if led_state is not None:
        break

if led_state is None:
    print("SYNC(boot) -> no reply yet (will keep listening)")

# ===== メインループ =====
while True:
    # 押して離したら toggle を送る（簡易デバウンス）
    if not boot_button.value():
        while not boot_button.value():
            time.sleep(0.01)
        send_cmd(b"toggle")
        time.sleep(0.2)  # チャタリング/多重送信抑止

    # STATE 受信で led_state を同期（LED制御はしない）
    host, msg = e.recv(20)
    if msg:
        try:
            bmsg = bytes(msg).strip()
        except Exception:
            bmsg = msg.tobytes().strip() if hasattr(msg, "tobytes") else msg

        if bmsg == b"STATE:ON":
            if led_state is not True:
                led_state = True
                print("SYNC -> LED ON")
        elif bmsg == b"STATE:OFF":
            if led_state is not False:
                led_state = False
                print("SYNC -> LED OFF")

    time.sleep(0.01)
