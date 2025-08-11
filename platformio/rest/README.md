# ESP32 REST API 学習

このプロジェクトは、PlatformIO環境でESP32を使用してREST APIサーバーを構築する学習用プロジェクトです。

## ビルドとアップロード

PlatformIO CLIまたはVSCodeのPlatformIO拡張機能を使用してビルドおよびアップロードが可能です。

```bash
# プロジェクトをビルドする
pio run

# デバイスにアップロードする
pio run -t upload
```

## 実行とIPアドレスの確認

1.  デバイスをPCに接続します。
2.  以下のコマンドでシリアルモニターを起動します。ボーレートは `115200` です。

    ```bash
    pio device monitor
    ```
3.  WiFiに接続後、シリアルモニターに以下のようにIPアドレスが表示されます。このIPアドレスを控えておきます。

    ```
    WiFi connected
    IP address: 192.168.0.123
    ```

## APIエンドポイント

ブラウザやcurlコマンドなどから、以下のURLにアクセスすることでESP32を操作できます。
IPアドレスの部分は、シリアルモニターで確認したご自身の環境のものに置き換えてください。

-   **LEDをオンにする**
    ```
    http://192.168.0.123/led/on
    ```
-   **LEDをオフにする**
    ```
    http://192.168.0.123/led/off
    ```
-   **LEDをリセットする (点滅)**
    ```
    http://192.168.0.123/led/reset
    ```

## ディレクトリ構成

```
.
├── include/      # ヘッダーファイル
├── lib/          # プロジェクト固有のライブラリ
├── src/          # メインのソースコード
├── test/         # テストコード
├── platformio.ini # PlatformIOプロジェクト設定ファイル
└── openapi.yaml  # API仕様書
