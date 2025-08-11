# ESP32 Wi-Fi LED Control v2

ESP32を使用して、Wi-Fi経由でLEDを制御するプロジェクトです。
このバージョンでは、Webインターフェースのデザインを改善し、HTML/CSSコードを分離してメンテナンス性を向上させています。

## 概要

ESP32がWebサーバーとして機能し、モダンなUIのWebページから、接続されたLEDをON/OFFします。

## ファイル構成

- `wifi_led2.ino`: メインのArduinoコード。WebサーバーとLED制御ロジックを実装。
- `config.h`: Wi-Fiの接続情報を設定するファイル。
- `index.h`: WebページのHTML構造を定義。
- `style.h`: Webページのスタイルを定義するCSSコード。
- `README.md`: このファイル。

## 必要なもの

*   ESP32 開発ボード
*   LED
*   抵抗 (必要に応じて)
*   ブレッドボード
*   ジャンパーワイヤー

## セットアップ

1.  `config.h-sample` を `config.h` にコピー（またはリネーム）します。
2.  `config.h` を開き、ご自身のWi-FiのSSIDとパスワードを設定します。
    ```c
    const char* ssid = "YOUR_WIFI_SSID";
    const char* password = "YOUR_WIFI_PASSWORD";
    ```
3.  Arduino IDEで `wifi_led2.ino` を開き、ボード設定をESP32に合わせてコンパイルし、書き込みます。

## 使い方

1.  書き込み後、シリアルモニターを起動します (ボーレート: 115200)。
2.  Wi-Fiに接続されると、ESP32のIPアドレスがシリアルモニターに表示されます。
3.  同じネットワークに接続されたPCやスマートフォンのブラウザで、表示されたIPアドレスにアクセスします。
4.  表示されたページのボタンをクリックすると、LEDが点灯/消灯します。