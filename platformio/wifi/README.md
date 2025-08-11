# ESP32 Wi-Fi LED Control

## 概要

このプロジェクトは、ESP32を使用してWi-Fiネットワークに接続し、Webサーバーを介してLEDを制御するサンプルアプリケーションです。WebブラウザからESP32にアクセスし、LEDのON/OFFを切り替えることができます。

## 機能

-   ESP32をWi-Fiアクセスポイントに接続
-   固定IPアドレスの設定
-   Webサーバーを起動し、HTTPリクエストを待ち受け
-   Webページ上のリンクからLEDをON/OFFする機能
-   LEDの現在の状態をWebページに表示

## 必要なもの

-   ESP32開発ボード
-   LED
-   PlatformIO IDEまたはArduino IDE

## セットアップと使用方法

1.  **リポジトリをクローン:**
    ```bash
    git clone https://github.com/katoy/study-esp32.git
    cd study-esp32/platformio/wifi
    ```

2.  **設定ファイルを作成:**
    `include/secrets.h` という名前でファイルを作成し、以下の内容を記述します。ご自身の環境に合わせてWi-FiのSSID、パスワード、およびネットワーク設定を更新してください。

    ```cpp
    #pragma once

    // Wi-Fi設定
    #define WIFI_SSID "YOUR_WIFI_SSID"
    #define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

    // 固定IPアドレス設定
    #include <IPAddress.h>
    IPAddress LOCAL_IP(192, 168, 1, 100);
    IPAddress GATEWAY(192, 168, 1, 1);
    IPAddress SUBNET(255, 255, 255, 0);
    IPAddress DNS1(8, 8, 8, 8);
    IPAddress DNS2(8, 8, 4, 4);
    ```

3.  **ビルドとアップロード:**
    PlatformIOを使用してプロジェクトをビルドし、ESP32にアップロードします。

4.  **動作確認:**
    -   シリアルモニターを開き、ESP32がWi-Fiに接続し、IPアドレスを取得したことを確認します。
    -   Webブラウザで `http://<ESP32のIPアドレス>` にアクセスします。
    -   表示されたWebページのリンクをクリックして、LEDがON/OFFするか確認します。

## ピン設定

-   **LED:** `GPIO 19`
