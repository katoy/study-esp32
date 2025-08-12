# ble_led

ESP32 + Arduino で BLE (Bluetooth Low Energy) を使って LED を制御するサンプルプロジェクトです。

## 概要

- ESP32 ボード上で BLE サーバーを立ち上げ、スマートフォン等から接続して LED の ON/OFF を制御できます。
- Arduino IDE でビルド・書き込みが可能です。

## ファイル構成

- `ble_led.ino` : メインの Arduino スケッチファイル

## 必要なもの

- ESP32 開発ボード
- Arduino IDE（ESP32 ボードマネージャ導入済み）
- スマートフォン等の BLE クライアントアプリ（例: nRF Connect）

## 使い方

1. Arduino IDE で `ble_led.ino` を開きます。
2. ボードタイプを「ESP32」に設定します。
3. ESP32 ボードを PC に接続し、スケッチを書き込みます。
4. スマートフォンの BLE アプリで ESP32 に接続し、LED の制御を行います。

### BLE クライアントアプリからの LED 制御操作例

例: nRF Connect を使用する場合

1. nRF Connect などの BLE クライアントアプリを起動し、ESP32（例: "ESP32_LED" など）に接続します。
2. サービス一覧から LED 制御用のキャラクタリスティック（例: UUID が 0xFFE1 など）を探します。
3. キャラクタリスティックに値を書き込みます。
	- LED ON: `0x01` または `1` を送信
	- LED OFF: `0x00` または `0` を送信
4. 書き込み後、ESP32 上の LED が点灯・消灯することを確認します。

※ 実際の UUID や書き込む値は `ble_led.ino` の実装に依存します。必要に応じてスケッチ内のコメント等も参照してください。

## ライセンス

MIT License
