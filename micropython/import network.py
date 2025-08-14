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

def set_led(state):
    led.value(state)
    # 状態をMQTTで通知
    client.publish(wifi_config.MQTT_TOPIC_STATUS, b"on" if state else b"off")

def mqtt_callback(topic, msg):
    if topic == wifi_config.MQTT_TOPIC_CMD.encode():
        if msg == b"on":
            set_led(1)
        elif msg == b"off":
            set_led(0)
        elif msg == b"status":
            # 状態を返す
            client.publish(wifi_config.MQTT_TOPIC_STATUS, b"on" if led.value() else b"off")

# メイン処理
connect_wifi()
client = MQTTClient("esp32", wifi_config.MQTT_BROKER, port=wifi_config.MQTT_PORT)
client.set_callback(mqtt_callback)
client.connect()
client.subscribe(wifi_config.MQTT_TOPIC_CMD)

print("MQTT connected, waiting for commands...")
while True:
    client.check_msg()
    time.sleep(0.1)