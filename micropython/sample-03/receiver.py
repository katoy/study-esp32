# receiver.py
import time
from machine import Pin
from espnow_common import init_espnow, add_broadcast_peer, recv_bytes, BCAST, CHANNEL

# ESP-NOW 初期化（ブロードキャスト登録）
e, sta = init_espnow(channel=CHANNEL)
add_broadcast_peer(e, channel=CHANNEL)
print("Receiver ready | ch:", sta.config('channel'), " | MAC:", sta.config('mac'))

# GPIO
LED_PIN    = 19
BUTTON_PIN = 0  # BOOT
led    = Pin(LED_PIN, Pin.OUT, value=0)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# デバウンス（押して離した瞬間でトグル）
DEBOUNCE_MS = 40
last_read = 1
stable_state = 1
last_change_ms = time.ticks_ms()

def bc_state(tag=b"state"):
    msg = b"STATE:ON" if led.value() else b"STATE:OFF"
    ok = e.send(BCAST, msg, True)
    print(b"BC["+tag+b"]", msg, "->", "OK" if ok else "FAIL")

def set_led(val: int, source=b"local"):
    val = 1 if val else 0
    if led.value() != val:
        led.value(val)
        print("LED", "ON" if val else "OFF", "(", source.decode() if isinstance(source, bytes) else source, ")")
        bc_state(tag=source if isinstance(source, bytes) else b"state")

def toggle_led(source=b"local"):
    set_led(0 if led.value() else 1, source=source)

# 起動時に現在状態を告知（任意）
time.sleep_ms(200)
bc_state(tag=b"boot")

# メインループ
while True:
    now = time.ticks_ms()

    # ボタン（押して離した瞬間）
    reading = button.value()
    if reading != last_read:
        last_change_ms = now
        last_read = reading
    if time.ticks_diff(now, last_change_ms) > DEBOUNCE_MS and reading != stable_state:
        prev = stable_state
        stable_state = reading
        if prev == 0 and stable_state == 1:
            toggle_led(source=b"button")

    # 受信（bytes 正規化）
    _, msg = recv_bytes(e, 20)
    if msg:
        if msg == b"on":
            set_led(1, source=b"remote")
        elif msg == b"off":
            set_led(0, source=b"remote")
        elif msg == b"toggle":
            toggle_led(source=b"remote")
        elif msg.upper() == b"ESP?":
            bc_state(tag=b"esp?")  # 起動同期要求に応答

    time.sleep_ms(2)
