import time
from espnow_utils import init_espnow

# ESP-NOWを初期化
e = init_espnow()

# 送信先のMACアドレス（ブロードキャスト）
peer = b'\xff\xff\xff\xff\xff\xff'
e.add_peer(peer)

print("Sending...")
while True:
    # メッセージ 'on' を送信
    print("Sending on...")
    if e.send(peer, b'on', True):
        print("Send success")
    else:
        print("Send fail")
    time.sleep(2)

    # メッセージ 'off' を送信
    print("Sending off...")
    if e.send(peer, b'off', True):
        print("Send success")
    else:
        print("Send fail")
    time.sleep(2)