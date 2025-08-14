
# ESP32 MicroPython LED制御 & MQTT連携サンプル

## 概要

このプロジェクトは、ESP32（MicroPython）とMac上のMQTTブローカー（mosquitto）を使い、
MacのコマンドラインからESP32のLED（GPIO19）をON/OFF制御したり、LEDの状態を取得するサンプルです。

---

## 構成

- Mac：mosquitto（MQTTブローカー）を起動
- ESP32：MicroPythonでMQTTクライアントとして動作
- MacのコマンドラインからMQTTメッセージ送信・受信

---

## ファイル構成

- `mqtt/wifi_config.py`
	WiFi・MQTTの設定（SSID、パスワード、ブローカーIPなど）
	※ 機密情報のため `.gitignore` でGit管理から除外しています。

- `mqtt/led_control.py`
	ESP32側のLED制御・MQTT受信プログラム

---

## 使い方

### 1. Macでmosquittoを起動

```sh
brew install mosquitto
brew services start mosquitto
```

設定ファイル `/usr/local/etc/mosquitto/mosquitto.conf` に
```
listener 1883
allow_anonymous true
```
を記載してください。

---

### 2. ESP32にMicroPythonファイルを書き込む

- `wifi_config.py` のSSID、パスワード、MQTT_BROKER（MacのIP）を編集
- `led_control.py` をESP32に転送し、実行

---

### 3. MacからLED制御・状態取得

#### LEDをON

```sh
mosquitto_pub -h <MacのIP> -p 1883 -t esp32/led/cmd -m "on"
```

#### LEDをOFF

```sh
mosquitto_pub -h <MacのIP> -p 1883 -t esp32/led/cmd -m "off"
```

#### LEDの状態を問い合わせ

```sh
mosquitto_pub -h <MacのIP> -p 1883 -t esp32/led/cmd -m "status"
```

#### LED状態を受信

```sh
mosquitto_sub -h <MacのIP> -p 1883 -t esp32/led/status
```

---

## 注意事項

- ESP32とMacは同じWiFiネットワークに接続してください。
- GPIO19にLEDを接続してください。
- MicroPythonのumqtt.simpleライブラリが必要です。
- 機密情報（wifi_config.py）はGit管理から除外しています。

---

## ライセンス

MIT License
