# wifi2 (ESP32 PlatformIO Project)

## 概要
ESP32を使ったWiFi接続・Webサーバー・LED制御のサンプルプロジェクトです。

- `/LED_ON` または `/LED_OFF` へのアクセスでLEDのON/OFFが可能
- ブラウザでアクセスすると `data/index.html` の内容が表示されます

## 必要な作業

### 1. SPIFFSファイルシステムイメージのアップロード
WebサーバーでHTMLファイル（`data/index.html`）を表示するには、SPIFFS領域にファイルを書き込む必要があります。

**必ず下記コマンドを実行してください：**

```
platformio run --target uploadfs
```

このコマンドを実行しないと、ESP32上でHTMLファイルが見つからず、Webページが正しく表示されません。

### 2. ファームウェアの書き込み

```
platformio run --target upload
```

### 3. シリアルモニタの利用
正しいシリアルポートを選択し、ESP32のログを確認してください。

## ディレクトリ構成

- `src/` : メインのC++ソースコード
- `data/` : SPIFFSにアップロードするWebファイル（例: index.html）
- `include/` : 設定ファイル（secrets.h など）

## 注意事項
- WiFi設定やIPアドレスは `include/secrets.h` で管理しています。
- SPIFFSアップロード後にファームウェア書き込みを行うと、SPIFFS内容が消える場合があります。必要に応じて再度 `uploadfs` を実行してください。

---

何か問題があれば、シリアルモニタの出力やエラーメッセージを確認してください。
