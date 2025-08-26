import time
from machine import Pin, PWM
import aioble
import network
from config import AP_CONFIG, BLE_CONFIG
import uasyncio as asyncio
import socket

# LED初期化（GPIO18, 19）
led1 = PWM(Pin(18), freq=1000)
led2 = PWM(Pin(19), freq=1000)
led_enabled = True
x_val = 0
y_val = 0
sw_val = 1

# Wi-Fi接続
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(AP_CONFIG.get('ssid', 'your-ssid'), AP_CONFIG.get('password', 'your-password'))
while not sta.isconnected():
    pass
ip_addr = sta.ifconfig()[0]
print('Wi-Fi connected. IP address:', ip_addr)

# BLE Centralとしてsenderに接続し、値をグローバル変数に反映
def set_leds():
    global led_enabled, x_val, y_val, sw_val
    x_percent = int((x_val / 4095) * 100)
    y_percent = int((y_val / 4095) * 100)
    led_enabled = (sw_val == 1)
    if led_enabled:
        led1.duty_u16(int(65535 * (x_percent / 100)))
        led2.duty_u16(int(65535 * (y_percent / 100)))
    else:
        led1.duty_u16(0)
        led2.duty_u16(0)

async def ble_loop():
    global x_val, y_val, sw_val
    while True:
        print('Scanning for joystick sender...')
        device = await aioble.scan(name=BLE_CONFIG.get('name', 'ESP32-Joystick'), timeout_ms=5000)
        if device:
            print('Found sender, connecting...')
            conn = await device.connect()
            service = await conn.service(0x180F)
            char = await service.characteristic(0x2A19)
            while True:
                data = await char.read()
                x_val = int.from_bytes(data[0:2], 'little')
                y_val = int.from_bytes(data[2:4], 'little')
                sw_val = data[4]
                set_leds()
                await asyncio.sleep(0.1)

# Webサーバ
async def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print(f'Web server listening on http://{ip_addr}:80')
    while True:
        cl, addr = s.accept()
        try:
            cl_file = cl.makefile('rwb', 0)
            request_line = cl_file.readline()
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
            if b'/status' in request_line:
                w_val = 0 if sw_val == 0 else 1
                json = '{{"x": {}, "y": {}, "w": {}, "led": {}}}'.format(x_val, y_val, w_val, int(led_enabled))
                cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json; charset=UTF-8\r\n\r\n')
                cl.send(json)
            elif b'/style.css' in request_line:
                with open('static/style.css', 'r') as f:
                    css = f.read()
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/css; charset=UTF-8\r\n\r\n')
                cl.send(css)
            elif b'/script.js' in request_line:
                with open('static/script.js', 'r') as f:
                    js = f.read()
                cl.send('HTTP/1.0 200 OK\r\nContent-type: application/javascript; charset=UTF-8\r\n\r\n')
                cl.send(js)
            else:
                with open('static/index.html', 'r') as f:
                    html = f.read()
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html; charset=UTF-8\r\n\r\n')
                cl.send(html)
        except Exception as e:
            print('Web server error:', e)
        finally:
            cl.close()

# 並列でBLE受信・Webサーバ起動
async def main():
    await asyncio.gather(ble_loop(), web_server())

asyncio.run(main())
