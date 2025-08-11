# ESP32 Wi-Fi LED Control

ESP32を使用して、Wi-Fi経由でLEDを制御するプロジェクトです。

## 概要

ESP32がWebサーバーとして機能し、Webブラウザからのリクエストに応じて、接続されたLEDをON/OFFします。

## 必要なもの

*   ESP32 開発ボード
*   LED
*   抵抗 (必要に応じて)
*   ブレッドボード
*   ジャンパーワイヤー

## セットアップ

1.  リポジトリをクローンまたはダウンロードします。
2.  `config.h-sample` を `config.h` にリネームします。
3.  `config.h` を開き、ご自身のWi-FiのSSIDとパスワードを設定します。
    ```c
    const char* ssid = "YOUR_WIFI_SSID";
    const char* password = "YOUR_WIFI_PASSWORD";
    ```
4.  Arduino IDEで `wifi_led.ino` を開き、ボード設定をESP32に合わせてコンパイルし、書き込みます。

## 使い方

1.  書き込み後、シリアルモニターを起動します (ボーレート: 115200)。
2.  Wi-Fiに接続されると、ESP32のIPアドレスがシリアルモニターに表示されます。
3.  同じネットワークに接続されたPCやスマートフォンのブラウザで、表示されたIPアドレスにアクセスします。
4.  表示されたページの "Turn ON" / "Turn OFF" リンクをクリックすると、LEDが点灯/消灯します。
