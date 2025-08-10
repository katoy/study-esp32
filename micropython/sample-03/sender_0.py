# sender.py
import time
from machine import Pin
from espnow_common import (
    init_espnow, add_peer_with_channel, to_bytes,
    send_cmd, ButtonDebouncer
)

CHANNEL = 1
BCAST   = b'\xff\xff\xff\xff\xff\xff'
BUTTON_PIN  = 0
SYNC_TRIES  = 3
SYNC_WAIT_MS = 300

# --- 初期化 ---
e, sta = init_espnow(channel=CHANNEL)
add_peer_with_channel(e, BCAST, channel=CHANNEL)
print("Sender ready | ch:", sta.config('channel'), " MAC:", sta.config('mac'))

# --- 入力（押して離したらトグル送信） ---
button = ButtonDebouncer(Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP), debounce_ms=40)

# --- 状態（受信同期用） ---
led_state = None  # None=未同期, True/False=同期済

# --- 起動時同期（ESP? -> STATE:ON/OFF を待つ） ---
for _ in range(SYNC_TRIES):
    send_cmd(e, BCAST, b"ESP?")
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < SYNC_WAIT_MS:
        host, msg = e.recv(50)
        if not msg:
            continue
        bmsg = to_bytes(msg)
        if bmsg == b"STATE:ON":
            led_state = True
            print("SYNC(boot) -> LED ON")
            break
        if bmsg == b"STATE:OFF":
            led_state = False
            print("SYNC(boot) -> LED OFF")
            break
    if led_state is not None:
        break
if led_state is None:
    print("SYNC(boot) -> no reply (will keep listening)")

# --- メインループ ---
while True:
    now = time.ticks_ms()

    # 押して離したら toggle 送信
    if button.update(now):
        send_cmd(e, BCAST, b"toggle")

    # STATE を受けたら led_state を更新（LEDは触らない）
    host, msg = e.recv(20)
    if msg:
        bmsg = to_bytes(msg)
        if bmsg == b"STATE:ON" and led_state is not True:
            led_state = True;  print("SYNC -> LED ON")
        elif bmsg == b"STATE:OFF" and led_state is not False:
            led_state = False; print("SYNC -> LED OFF")

    time.sleep_ms(5)
