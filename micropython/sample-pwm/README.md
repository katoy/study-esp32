# ESP32 Joystick & LED BLE/Webサーバ サンプル

## 概要
ESP32を2台使い、ジョイスティック値をBLEで送信し、受信側でLED2つの明るさ制御＋Webサーバで状態表示を行うサンプルです。

- sender: ジョイスティック（ADC, SW）値をBLEで送信
- receiver: BLEで値を受信しLED制御＋Webサーバでリアルタイム表示
- BLE通信はaioble v0.6.1を使用
- ネットワーク設定はconfig.pyで管理

## ファイル構成

### メインプログラム
- `sender_ble_joystick.py`: ジョイスティックのX/Y軸の値とボタンの状態を読み取り、BLEで継続的に送信（Peripheral役）。
- `receiver_ble_led_server.py`: `sender_ble_joystick.py` からのBLE通知を受信し、2つのLEDの明るさをPWM制御します。ボタンの押下でLEDのON/OFFを切り替えます。
- `ap_led_with_joystick.py`: BLE受信とWebサーバ機能を組み合わせたサンプル。ジョイスティックの状態をWebページでリアルタイムに確認できます。
- `web_server_led_and_joystick.py`: ESP32に接続されたジョイスティックとLEDを直接制御し、その状態をWebサーバで表示する単体動作サンプル。

### toio連携
- `sender_toio_motor.py`: ジョイスティックの値をtoioのモーター制御コマンドに変換してBLEで送信します。
- `toio_controller_aioble.py`: toioとBLE通信を行うためのコントローラライブラリ。モーター、LED、サウンドなどの制御機能を提供します。
- `toio_led_blink_test.py`: `toio_controller_aioble.py` を使用して、toioのLEDを点滅させるテスト用スクリプト。
- `toio_motor_test.py`: `toio_controller_aioble.py` を使用して、toioのモーターを制御するテスト用スクリプト。

### テスト・ユーティリティ
- `joystick.py`: ジョイスティックのX/Y軸、ボタンの状態を読み取り、コンソールに表示する単体テスト用スクリプト。
- `led_18_19.py`: GPIO18, 19に接続された2つのLEDの明るさをPWMで滑らかに変化させるテスト用スクリプト。
- `led_with_joystick.py`: 1台のESP32でジョイスティックの値を読み取り、直接LEDの明るさを制御するサンプル。

### 設定・Webフロントエンド
- `config.py-sample`: Wi-FiのSSID/パスワードや、BLEのデバイス名を設定するためのサンプルファイル。`config.py`にリネームして使用します。
- `static/`: Webサーバ用のフロントエンドファイル群。
    - `index.html`: ジョイスティックの状態を表示するWebページのHTML。
    - `style.css`: Webページのスタイルシート。
    - `script.js`: サーバに状態を問い合わせ、Webページを動的に更新するJavaScript。

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

## Web機能について
Webサーバ機能の実装例は `web_server_led_and_joystick.py` を参照してください。
- LED・ジョイスティック値のリアルタイム表示
- HTML/JavaScript/CSSは static/ 配下に分離
- APIエンドポイント `/status` で値取得

## 注意事項
- aioble v0.6.1は標準16bit UUIDのみサポート
- BLE通信が不安定な場合はMicroPython本体・aiobleのバージョン整合性を確認
- Web画面はstatic/配下のファイルを利用

## ライセンス
MIT

## 作者
katoy
