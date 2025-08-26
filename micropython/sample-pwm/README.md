# ESP32 Joystick & LED BLE/Webサーバ サンプル

## 概要
ESP32を2台使い、ジョイスティック値をBLEで送信し、受信側でLED2つの明るさ制御＋Webサーバで状態表示を行うサンプルです。

- sender: ジョイスティック（ADC, SW）値をBLEで送信
- receiver: BLEで値を受信しLED制御＋Webサーバでリアルタイム表示
- BLE通信はaioble v0.6.1を使用
- ネットワーク設定はconfig.pyで管理

## ファイル構成
- sender_ble_joystick.py : ジョイスティック値をBLE送信
- receiver_ble_led_server.py : BLE受信→LED制御＋Webサーバ
- ap_led_with_joystick.py : BLE受信＋Webサーバ（サーバ構成例）
- web_server_led_and_joystick.py : Webサーバ単体サンプル
- static/index.html, style.css, script.js : Web画面用
- config.py : Wi-Fi/BLE設定

## 必要環境
- ESP32（MicroPython最新版推奨）
- aioble v0.6.1（lib/aioble/ 配置）
- uasyncio, network, machine（MicroPython標準）

## インストール手順
1. MicroPython最新版をESP32に書き込み
2. aioble（v0.6.1）をlib/に配置（GitHubから取得）
3. 本リポジトリのファイルをESP32に転送
4. config.pyでWi-Fi/BLE設定を編集

## 使い方
### sender側（ジョイスティック）
1. sender_ble_joystick.pyを実行
2. BLEでジョイスティック値・SW状態を送信

### receiver側（LED＋Webサーバ）
1. receiver_ble_led_server.pyまたはap_led_with_joystick.pyを実行
2. BLEで値を受信しLED制御
3. Webサーバ（http://<IPアドレス>:80）で状態をリアルタイム表示

## 注意事項
- aioble v0.6.1は標準16bit UUIDのみサポート
- BLE通信が不安定な場合はMicroPython本体・aiobleのバージョン整合性を確認
- Web画面はstatic/配下のファイルを利用

## ライセンス
MIT

## 作者
katoy
