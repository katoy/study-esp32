# receiver.py — BC受信 / 押して離したらトグル / 変更時にSTATE送信 / ESP?応答
from machine import Pin
from espnow_utils import init_espnow, add_peer_with_channel
import time

CHANNEL = 1
BCAST   = b'\xff\xff\xff\xff\xff\xff'

LED_PIN    = 19
BUTTON_PIN = 0   # BOOT

led = Pin(LED_PIN, Pin.OUT, value=0)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# デバウンス
DEBOUNCE_MS = 40
last_read = 1
stable_state = 1
last_change_ms = time.ticks_ms()

# ESP-NOW
e, sta = init_espnow(channel=CHANNEL)
add_peer_with_channel(e, BCAST, channel=CHANNEL)

def broadcast_state(tag="state"):
    msg = b"STATE:ON" if led.value() else b"STATE:OFF"
    ok = e.send(BCAST, msg, True)
    print(f"Broadcast({tag})", msg, "->", "OK" if ok else "FAIL")

def set_led(val, source="local"):
    val = 1 if val else 0
    if led.value() != val:
        led.value(val)
        print(f"LED {'ON' if val else 'OFF'} ({source})")
        broadcast_state(tag=source)

def toggle_led(source="local"):
    set_led(0 if led.value() else 1, source=source)

print("Receiver ready | ch:", sta.config('channel'), " | MAC:", sta.config('mac'))

# 起動直後に現在状態を一度知らせておく（任意）
broadcast_state(tag="boot")

while True:
    now = time.ticks_ms()

    # 押して離した瞬間でトグル
    reading = button.value()
    if reading != last_read:
        last_change_ms = now
        last_read = reading
    if time.ticks_diff(now, last_change_ms) > DEBOUNCE_MS and reading != stable_state:
        prev = stable_state
        stable_state = reading
        if prev == 0 and stable_state == 1:
            toggle_led(source="button")

    # 受信
    host, msg = e.recv(20)
    if msg:
        try:
            bmsg = bytes(msg).strip()
        except Exception:
            bmsg = msg.tobytes().strip() if hasattr(msg, "tobytes") else msg

        # コマンド処理
        if bmsg == b"on":
            set_led(1, source="remote")
        elif bmsg == b"off":
            set_led(0, source="remote")
        elif bmsg == b"toggle":
            toggle_led(source="remote")
        elif bmsg.upper() == b"ESP?":
            # 起動時同期要求に応答（現在状態を送る）
            broadcast_state(tag="esp?")
        # 既存：STATE:* を受けた場合は何もしないでOK（冪等）

    time.sleep_ms(2)
