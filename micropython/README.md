# ESP32 MicroPython LED制御 & MQTT連携サンプル

## 概要

このプロジェクトは、ESP32（MicroPython）とMac上のMQTTブローカー（mosquitto）を使い、
MacのコマンドラインからESP32のLED（GPIO19）をON/OFF制御・状態取得できるサンプルです。加えて BOOT ボタン(GPIO0) を押すことでローカルでも LED をトグルでき、状態変化は常に MQTT の `esp32/led/status` トピックへ publish されます（デバウンス対応）。

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
	ESP32側のLED制御・MQTT受信 / BOOTボタントグル / デバウンス（約80ms） / 状態自動publish

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

#### BOOTボタンでのローカル操作

ESP32基板上の BOOT ボタン(GPIO0) を押下すると LED がトグルし、その都度 `esp32/led/status` に `on` / `off` が publish されます。

---

## 注意事項

- ESP32とMacは同じWiFiネットワークに接続してください。
- GPIO19 に LED（アノードをGPIO19、カソードを抵抗経由で GND）を接続してください。
- MicroPythonのumqtt.simpleライブラリが必要です。
- 機密情報（wifi_config.py）はGit管理から除外しています。
- BOOTボタンはプルアップ入力のため「押下 = Low」になります。

---

## トラブルシュート

| 症状 | 確認ポイント | 対処 |
|------|--------------|------|
| 接続時に `ECONNRESET` | mosquitto がLAN待受か | `lsof -i :1883` で `*` LISTEN を確認 |
| `Connection refused` | ブローカー未起動 | `mosquitto -v` で手動起動 |
| status 応答なし | publish / subscribe トピック名 | `esp32/led/cmd` / `esp32/led/status` を再確認 |
| BOOTボタン反応しない | GPIO0 割込み無効化/配線 | 電源再投入 / スクリプト再書込み |
| LED点灯が逆 | LEDの極性 | `led.value(1)` で点灯するか確認し逆なら配線確認 |

ログ観察: REPLで実行し `WiFi connected:` / `MQTT connected` が表示されるか確認してください。

---

## ライセンス

MIT License
