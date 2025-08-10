# sender.py
import time
from machine import Pin
from espnow_common import (
    init_espnow, add_broadcast_peer, recv_bytes,
    BCAST, CHANNEL, CMD_TOGGLE, CMD_STATE_REQ, STATE_ON, STATE_OFF
)

# --- 初期化 ---
e, sta = init_espnow(channel=CHANNEL)
add_broadcast_peer(e, channel=CHANNEL)
mac_hex = sta.config('mac').hex()
mac_str = ':'.join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
print(f"Sender ready | ch: {sta.config('channel')} | MAC: {mac_str}")

BUTTON_PIN = 0
btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# --- グローバル変数 ---
led_state = None  # None:未同期, True/False:同期済み

# --- 関数 ---
def send_cmd(cmd: bytes):
    """コマンドをブロードキャスト送信"""
    cmd = bytes(cmd).strip()
    ok = e.send(BCAST, cmd, True)
    print(f"TX {cmd!r} -> {'OK' if ok else 'FAIL'}")
    return ok

def sync_state_on_boot(timeout_ms=400, retries=3):
    """起動時に受信機とLED状態を同期する"""
    global led_state
    print("SYNC(boot) start")
    for i in range(retries):
        send_cmd(CMD_STATE_REQ)
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            _, msg = recv_bytes(e, 50)
            if msg == STATE_ON:
                led_state = True
                print("SYNC(boot) -> LED ON")
                return
            elif msg == STATE_OFF:
                led_state = False
                print("SYNC(boot) -> LED OFF")
                return
            time.sleep_ms(5)
    print("SYNC(boot) -> no reply (keep listening)")

def handle_button_press():
    """ボタンが押されて離されたらtoggleコマンドを送信"""
    if not btn.value():  # 押下
        time.sleep_ms(20) # 簡易デバウンス
        while not btn.value():  # 離すのを待つ
            time.sleep_ms(10)
        send_cmd(CMD_TOGGLE)
        time.sleep_ms(200)  # 送信後のチャタリング抑止

def handle_state_sync():
    """受信機からの状態通知を処理してローカルの状態を更新"""
    global led_state
    _, msg = recv_bytes(e, 20)
    if msg == STATE_ON:
        if led_state is not True:
            led_state = True
            print("SYNC -> LED ON")
    elif msg == STATE_OFF:
        if led_state is not False:
            led_state = False
            print("SYNC -> LED OFF")

# --- メイン処理 ---
time.sleep_ms(300)  # 起動直後の取りこぼし回避
sync_state_on_boot()

while True:
    handle_button_press()
    handle_state_sync()
    time.sleep_ms(10)
