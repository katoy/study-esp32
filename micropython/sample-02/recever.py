import network
import espnow
from machine import Pin
import time

# --- 1. ネットワークインターフェースを強制リセット ---
print("ネットワークインターフェースをリセット中...")
ap = network.WLAN(network.AP_IF)
ap.active(False)
sta = network.WLAN(network.STA_IF)
sta.active(False)
time.sleep(1)

# --- 2. Wi-Fi (STAモード) を初期化 ---
print("Wi-Fiを初期化中...")
sta.active(True)
sta.config(channel=1) # チャンネルを1に固定
time.sleep(1)

# --- 3. ESP-NOWを初期化 ---
print("ESP-NOWを初期化中...")
e = espnow.ESPNow()
e.active(True)

# --- 4. LEDピンを設定 ---
led = Pin(19, Pin.OUT)

# --- 5. 起動情報を表示 ---
print("\n--- ESP-NOW 受信準備完了 ---")
print("MACアドレス:", sta.config('mac').hex())
print("Wi-Fiチャンネル:", sta.config('channel'))
print("---------------------------")

# --- 6. メッセージ受信ループ (5秒タイムアウト付き) ---
while True:
    host, msg = e.recv(5000)  # 5000ミリ秒 = 5秒のタイムアウト
    
    if msg:
        # メッセージ受信成功
        print(f"受信成功！ 送信元: {host.hex()}, メッセージ: {msg}")
        if msg == b'on':
            print("LEDをONにします")
            led.on()
        elif msg == b'off':
            print("LEDをOFFにします")
            led.off()
    else:
        # タイムアウトした場合
        print("受信待機中... (タイムアウト)")