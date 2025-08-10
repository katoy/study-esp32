import time
from machine import Pin
from espnow_utils import init_espnow

# ESP-NOWを初期化
e = init_espnow()

# 送信先のMACアドレス（ブロードキャスト）
peer = b'\xff\xff\xff\xff\xff\xff'
e.add_peer(peer)

# LEDピンを設定
led = Pin(2, Pin.OUT)
# BOOTボタンピンを設定
boot_button = Pin(0, Pin.IN, Pin.PULL_UP)

led_state = False # False: off, True: on

print("Ready to send. Press and release the BOOT button.")

while True:
    if not boot_button.value(): # ボタンが押された (LOW)
        # ボタンが離されるまで待つ
        while not boot_button.value():
            time.sleep(0.01)
        
        # ボタンが離されたのでアクションを実行
        # LEDの状態をトグル
        led_state = not led_state
        led.value(led_state)

        # メッセージを送信
        msg = 'on' if led_state else 'off'
        print(f"Sending {msg}...")
        if e.send(peer, msg.encode(), True):
            print("Send success")
        else:
            print("Send fail")
        
        # チャタリング防止
        time.sleep(0.2)

    time.sleep(0.01)
