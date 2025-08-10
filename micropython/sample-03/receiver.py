# receiver.py
import time
from machine import Pin
from espnow_common import (
    init_espnow, add_broadcast_peer, recv_bytes,
    BCAST, CHANNEL, CMD_ON, CMD_OFF, CMD_TOGGLE, CMD_STATE_REQ, STATE_ON, STATE_OFF
)

# --- 初期化 ---
e, sta = init_espnow(channel=CHANNEL)
add_broadcast_peer(e, channel=CHANNEL)
mac_hex = sta.config('mac').hex()
mac_str = ':'.join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
print(f"Receiver ready | ch: {sta.config('channel')} | MAC: {mac_str}")

LED_PIN = 19
BUTTON_PIN = 0
led = Pin(LED_PIN, Pin.OUT, value=0)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# --- 関数 ---
def broadcast_state(tag=b"state"):
    """現在のLEDの状態をブロードキャスト"""
    msg = STATE_ON if led.value() else STATE_OFF
    ok = e.send(BCAST, msg, True)
    print(f"BC[{tag.decode()}] {msg!r} -> {'OK' if ok else 'FAIL'}")

def set_led(val: int, source="local"):
    """LEDの状態を設定し、変更があれば通知"""
    val = 1 if val else 0
    if led.value() != val:
        led.value(val)
        print(f"LED {'ON' if val else 'OFF'} (by {source})")
        broadcast_state(tag=source.encode() if isinstance(source, str) else source)

def toggle_led(source="local"):
    """LEDの状態をトグル"""
    set_led(not led.value(), source=source)

def handle_button_press():
    """ボタンが押されて離されたらLEDをトグル"""
    if not button.value():  # 押下
        time.sleep_ms(50)  # デバウンス
        if not button.value():
            while not button.value():  # 離すのを待つ
                time.sleep_ms(10)
            toggle_led(source="button")

def handle_received_commands():
    """受信したコマンドを処理"""
    _, msg = recv_bytes(e, 20)
    if not msg:
        return

    if msg == CMD_ON:
        set_led(1, source="remote")
    elif msg == CMD_OFF:
        set_led(0, source="remote")
    elif msg == CMD_TOGGLE:
        toggle_led(source="remote")
    elif msg == CMD_STATE_REQ:
        broadcast_state(tag="esp?")

# --- メイン処理 ---
time.sleep_ms(200)
broadcast_state(tag=b"boot")

while True:
    handle_button_press()
    handle_received_commands()
    time.sleep_ms(10)
