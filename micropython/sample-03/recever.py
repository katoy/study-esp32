from machine import Pin
from espnow_utils import init_espnow

# LEDピンを設定
led = Pin(19, Pin.OUT)

# ESP-NOWを初期化
e = init_espnow()

print("Waiting for messages...")
while True:
    host, msg = e.recv()
    if msg:
        print(f"Received message from: {host.hex()}, message: {msg}")
        if msg == b'on':
            print("LED ON")
            led.on()
        elif msg == b'off':
            print("LED OFF")
            led.off()