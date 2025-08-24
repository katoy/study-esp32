import network
import socket
from config import AP_CONFIG
from machine import Pin, ADC
import time

# Wi-Fi接続
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(AP_CONFIG.get('ssid', 'your-ssid'), AP_CONFIG.get('password', 'your-password'))
while not sta.isconnected():
    pass
ip_addr = sta.ifconfig()[0]
print('Wi-Fi connected. IP address:', ip_addr)
print(f'Web server URL: http://{ip_addr}:80')

# ジョイスティック・LED初期化
joystick_x = ADC(Pin(34))
joystick_y = ADC(Pin(35))
joystick_btn = Pin(33, Pin.IN, Pin.PULL_UP)
joystick_x.atten(ADC.ATTN_11DB)
joystick_y.atten(ADC.ATTN_11DB)

# Webサーバ

def start_web_server():
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
                x_val = joystick_x.read()
                y_val = joystick_y.read()
                w_val = 0 if joystick_btn.value() == 0 else 1
                json = '{{"x": {}, "y": {}, "w": {}}}'.format(x_val, y_val, w_val)
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

start_web_server()

# メインスレッドが終了しないようにする
while True:
    pass
document.getElementById('wval').textContent = data.w;
