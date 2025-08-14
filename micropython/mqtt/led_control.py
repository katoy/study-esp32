import network
import time
from machine import Pin
from umqtt.simple import MQTTClient
import wifi_config

# WiFi接続
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi_config.WIFI_SSID, wifi_config.WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi connected:", wlan.ifconfig())

# LED制御
led = Pin(19, Pin.OUT)

# BOOTボタン(GPIO0)でLEDトグル用（プルアップなので押下で Low）
button = Pin(0, Pin.IN, Pin.PULL_UP)

# デバウンス管理
_last_press_ms = 0
_press_flag = False
_need_status_publish = False  # LED状態をMQTTへ送る要求フラグ

def _button_irq(pin):
    # IRQ内では重い処理(MQTT publish)をしない。フラグだけ。
    global _last_press_ms, _press_flag
    now = time.ticks_ms()
    # 80ms デバウンス
    if time.ticks_diff(now, _last_press_ms) > 80:
        _last_press_ms = now
        _press_flag = True

def set_led(state):
    global _need_status_publish
    led.value(state)
    _need_status_publish = True  # 実際のpublishはメインループで実行

def publish_status():
    # 状態publishを集中管理し、例外を表示して原因を把握しやすくする
    payload = b"on" if led.value() else b"off"
    client.publish(wifi_config.MQTT_TOPIC_STATUS, payload)
    #print('[DBG] published status', payload)

def mqtt_callback(topic, msg):
    if topic == wifi_config.MQTT_TOPIC_CMD.encode():
        if msg == b"on":
            set_led(1)
        elif msg == b"off":
            set_led(0)
        elif msg == b"status":
            publish_status()

# メイン処理
connect_wifi()
client = MQTTClient("esp32", wifi_config.MQTT_BROKER, port=wifi_config.MQTT_PORT, keepalive=30)
client.set_callback(mqtt_callback)
client.connect()
client.subscribe(wifi_config.MQTT_TOPIC_CMD)

# ボタンIRQ登録（接続後に設定）
button.irq(trigger=Pin.IRQ_FALLING, handler=_button_irq)

print("MQTT connected, waiting for commands...")
_last_ping_ms = time.ticks_ms()

while True:
    # MQTT受信処理（非ブロッキング）
    try:
        client.check_msg()
    except Exception as e:
        print('[ERR] check_msg', e)

    # ボタン押下フラグ処理（メインループ側でトグル）
    if _press_flag:
        _press_flag = False
        new_state = 0 if led.value() else 1
        set_led(new_state)

    # 状態publish要求があれば送信
    if _need_status_publish:
        try:
            publish_status()
        except Exception as e:
            print('[ERR] publish_status', e)
        _need_status_publish = False

    # 定期PINGで接続維持（keepalive補助）
    if time.ticks_diff(time.ticks_ms(), _last_ping_ms) > 10000:  # 10s
        try:
            client.ping()
            #print('[DBG] ping')
        except Exception as e:
            print('[ERR] ping', e)
        _last_ping_ms = time.ticks_ms()

    time.sleep(0.02)