# ESP32 学習リポジトリ

このリポジトリは、ESP32 の開発を学習するためのものです。

## ディレクトリ構成

- `arduino/`: Arduino IDE を使用したサンプルプロジェクト
- `platformio/`: PlatformIO を使用したサンプルプロジェクト
- `web_page/`: ESP32でホストするWebページのサンプル

## 各プロジェクトの詳細

### arduino/sample

LEDを点滅させるシンプルなスケッチです。

### arduino/wifi_led

WiFiに接続し、LEDを制御するためのシンプルなWebサーバーを起動します。

### platformio/esp32-led

LEDを点滅させるシンプルなPlatformIOプロジェクトです。

### platformio/rest

LEDを制御するためのRESTful APIを提供するPlatformIOプロジェクトです。静的IPアドレスを使用します。

### platformio/wifi

WiFiに接続し、LEDを制御するためのシンプルなWebサーバーを起動するPlatformIOプロジェクトです。静的IPアドレスを使用します。

### web_page/index.html

`platformio/rest`プロジェクトを実行しているESP32のLEDを制御するために使用できるWebページです。
