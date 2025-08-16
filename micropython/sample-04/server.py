"""ESP32 AP + LED 制御 + REST API + 物理ボタン (GPIO0) トグル

curl http://192.168.4.1/api/led
curl -X POST 'http://192.168.4.1/api/led?state=on'
curl -X POST 'http://192.168.4.1/api/led?state=off'
"""

import network
import socket
import machine
import time

# ===== 設定 =====
SSID = 'MyESP32AP'
PASSWORD = 'password123'
IP_ADDR = '192.168.4.1'
SUBNET = '255.255.255.0'
GATEWAY = '192.168.4.1'
DNS = '8.8.8.8'
LED_PIN = 19
BUTTON_PIN = 0
DEBOUNCE_MS = 120
LED_ACTIVE_LOW = False
_HTML_TEMPLATE_CACHE = None  # index.html キャッシュ


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD)
    ap.ifconfig((IP_ADDR, SUBNET, GATEWAY, DNS))
    print('[LOG] AP started. IP:', ap.ifconfig()[0])
    return ap


def dumps_json(o):
    try:
        import ujson as json
    except ImportError:
        import json
    return json.dumps(o)


led = machine.Pin(LED_PIN, machine.Pin.OUT)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
last_press = 0  # デバウンス用最終押下時刻(ms)


def _is_led_on():
    v = led.value()
    return (v == 0) if LED_ACTIVE_LOW else (v == 1)


def _apply_led(on: bool):
    if LED_ACTIVE_LOW:
        led.value(0 if on else 1)
    else:
        led.value(1 if on else 0)
    # 状態確認ログ
    print(f'[LOG] LED状態 => {"ON" if _is_led_on() else "OFF"}')


def button_handler(pin):
    global last_press
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press) < DEBOUNCE_MS:
        return
    last_press = now
    if pin.value() == 0:  # 押下
        _apply_led(not _is_led_on())
        print('[LOG] ボタン: トグル ->', 'ON' if _is_led_on() else 'OFF')


button.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_handler)


def build_html():
    """index.html テンプレートを読み込み LED 状態プレースホルダを置換して返す。"""
    global _HTML_TEMPLATE_CACHE
    if _HTML_TEMPLATE_CACHE is None:
        try:
            with open('index.html', 'r') as f:
                _HTML_TEMPLATE_CACHE = f.read()
        except Exception as e:  # noqa
            return '<html><body><p>Template load error: ' + str(e) + '</p></body></html>'
    on = _is_led_on()
    return (_HTML_TEMPLATE_CACHE
            .replace('{{PIN}}', str(LED_PIN))
            .replace('{{STATE_CLASS}}', 'on' if on else 'off')
            .replace('{{STATE_TEXT}}', 'ON' if on else 'OFF'))


# ===== HTTP ユーティリティ =====

def _sendall(conn, data: bytes):
    mv = memoryview(data)
    sent_total = 0
    while sent_total < len(mv):
        n = conn.send(mv[sent_total:])
        if not n:
            raise OSError('send failed')
        sent_total += n


def _send_response(conn, status: str, content_type: str, body_bytes: bytes):
    headers = (
        'HTTP/1.1 ' + status + '\r\nContent-Type: ' + content_type + '\r\n'
        'Cache-Control: no-store\r\n'
        'Content-Length: ' + str(len(body_bytes)) + '\r\nConnection: close\r\n\r\n'
    )
    _sendall(conn, headers.encode() + body_bytes)


def _send_json(conn, obj):
    _send_response(conn, '200 OK', 'application/json; charset=utf-8', dumps_json(obj).encode())


def _send_html(conn, html: str, status='200 OK'):
    _send_response(conn, status, 'text/html; charset=utf-8', html.encode('utf-8'))


def _parse_query(q: str):
    params = {}
    if not q:
        return params
    for part in q.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            params[k] = v
        else:
            params[part] = ''
    return params


def handle_client(conn):
    try:
        # ヘッダ終端(\r\n\r\n) まで 1秒以内で待つ簡易ループ
        start = time.ticks_ms()
        buf = b''
        while True:
            chunk = conn.recv(512)
            if chunk:
                buf += chunk
                if b'\r\n\r\n' in buf or len(buf) > 2048:
                    break
            else:
                if time.ticks_diff(time.ticks_ms(), start) > 1000:
                    print('[DBG] request wait timeout; received bytes:', len(buf))
                    break
                time.sleep_ms(10)
                continue
        if not buf:
            return
        waited = time.ticks_diff(time.ticks_ms(), start)
        first = buf.split(b'\r\n', 1)[0].decode('utf-8', 'ignore')
        if waited > 50:
            print(f'[DBG] waited {waited}ms for first line')
        req = buf
        print('[LOG] Request:', first)
        parts = first.split(' ')
        if len(parts) < 2:
            return
        method = parts[0]
        raw_path = parts[1]
        # パス + クエリ分離
        query_str = ''
        if '?' in raw_path:
            path, query_str = raw_path.split('?', 1)
        else:
            path = raw_path
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        params = _parse_query(query_str)

        # REST GET (状態取得 / 任意で state= を許容)
        if method == 'GET' and path == '/api/led':
            st = params.get('state')
            if st == 'on':
                _apply_led(True)
                print('[LOG] API GET set -> on')
            elif st == 'off':
                _apply_led(False)
                print('[LOG] API GET set -> off')
            elif st == 'toggle':
                _apply_led(not _is_led_on())
                print('[LOG] API GET toggle')
            _send_json(conn, {'led': 'on' if _is_led_on() else 'off'})
            return

        # REST POST (on/off/toggle)
        if method == 'POST' and path == '/api/led':
            # クエリ(state=xxx) 優先 / 本文フォールバック
            body_txt = req.decode('utf-8', 'ignore')
            st = params.get('state')
            if not st:
                # 簡易本文解析
                if 'state=on' in body_txt:
                    st = 'on'
                elif 'state=off' in body_txt:
                    st = 'off'
                elif 'state=toggle' in body_txt:
                    st = 'toggle'
            if st == 'on':
                _apply_led(True)
                print('[LOG] API POST set -> on')
            elif st == 'off':
                _apply_led(False)
                print('[LOG] API POST set -> off')
            elif st == 'toggle':
                _apply_led(not _is_led_on())
                print('[LOG] API POST toggle')
            else:
                print('[WARN] API POST no valid state param')
            _send_json(conn, {'led': 'on' if _is_led_on() else 'off'})
            return

        # favicon
        if path == '/favicon.ico':
            _sendall(conn, b'HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n')
            return

        # CSS
        if path == '/style.css':
            try:
                with open('style.css','r') as f:
                    css = f.read()
            except Exception as e:  # noqa
                css = '/* missing style.css:' + str(e) + ' */'
            _send_response(conn, '200 OK', 'text/css; charset=utf-8', css.encode())
            return

        # 旧 /led/* パス互換 (キャッシュされた古い UI 対策)
        if path.startswith('/led/'):
            _send_html(conn, "<!DOCTYPE html><html><head><meta charset='utf-8'><meta http-equiv='refresh' content='0;url=/'></head><body style='font-family:Arial'>/led/* は廃止されました。<a href='/'>戻る</a></body></html>", '302 Found')
            return

        # 診断ページ
        if path == '/diag':
            logical = 'ON' if _is_led_on() else 'OFF'
            _send_html(conn, (
                "<!DOCTYPE html><html><body><h3>Diag</h3><p>raw=" + str(led.value()) +
                " logical=" + logical + " ACTIVE_LOW=" + str(LED_ACTIVE_LOW) +
                "</p><p><a href='/'>back</a></p></body></html>"
            ))
            return
        # 通常(ルートなど)ページ (ここまで return されなければルート扱い)
        html = build_html()
        print('[DBG] HTML length:', len(html))
        _send_html(conn, html)
    except Exception as e:
        print('[ERR]', type(e).__name__, e)
        try:
            conn.send('HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\n')
        except:  # noqa
            pass
    finally:
        try:
            conn.close()
        except:  # noqa
            pass


def run():
    setup_ap()
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(3)
    print('[LOG] Web server listening on :80')
    while True:
        try:
            conn, addr = s.accept()
            print('[LOG] Connection from', addr)
            # 受信開始前に僅かな待機で初回クリック時の遅延送信を緩和
            try:
                time.sleep_ms(15)
            except:  # noqa
                pass
            handle_client(conn)
        except Exception as e:
            print('[ERR main]', e)


run()