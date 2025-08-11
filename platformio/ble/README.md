# study-esp32 BLE Project

このリポジトリは、ESP32 を使った BLE (Bluetooth Low Energy) プロジェクトのサンプルです。

## ディレクトリ構成

- `src/` : メインのソースコード (`main.cpp` など)
- `include/` : ヘッダファイル
- `lib/` : 外部ライブラリ
- `test/` : テストコード
- `platformio.ini` : PlatformIO 設定ファイル
- `start-server.sh` : サーバ起動用スクリプト
- `index.html`, `script.js` : Web UI 関連ファイル

## 開発環境

- [PlatformIO](https://platformio.org/)
- ESP32 開発ボード


## ビルド & 書き込み

```sh
# ビルド
platformio run

# 書き込み
platformio run --target upload
```

## Webサーバの起動と操作方法

`start-server.sh` を実行すると、ローカルでWebサーバが起動します。

```sh
./start-server.sh
```

ブラウザで [http://localhost:8000/](http://localhost:8000/) にアクセスすると、
BLEデバイスとのペアリングや、LEDの ON / OFF 操作が可能です。

1. 「ペアリング」ボタンでESP32と接続
2. 「LED ON」「LED OFF」ボタンでLEDの制御

※ 詳細な操作方法や動作要件は `index.html` や `script.js` を参照してください。

## ライセンス

MIT License
