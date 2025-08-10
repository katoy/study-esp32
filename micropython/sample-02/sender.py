import network
import espnow
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

# --- 4. 送信先ピアを追加 ---
peer_mac = b'\xff\xff\xff\xff\xff\xff'  # ブロードキャストアドレス
try:
    e.add_peer(peer_mac)
except OSError:
    pass # ピアが既に存在していてもOK

# --- 5. 起動情報を表示 ---
print("\n--- ESP-NOW 送信準備完了 ---")
print("送信先ピア:", peer_mac.hex())
print("Wi-Fiチャンネル:", sta.config('channel'))
print("---------------------------")

# --- 6. メッセージ送信ループ (送信結果の確認付き) ---
while True:
    # メッセージ 'on' を送信
    print("メッセージ 'on' を送信します...")
    is_sent_on = e.send(peer_mac, b'on')
    if is_sent_on:
        print("  -> 送信成功")
    else:
        print("  -> 送信失敗")
    time.sleep(2)

    # メッセージ 'off' を送信
    print("メッセージ 'off' を送信します...")
    is_sent_off = e.send(peer_mac, b'off')
    if is_sent_off:
        print("  -> 送信成功")
    else:
        print("  -> 送信失敗")
    time.sleep(2)