# ESP32 LED PlatformIO Project

このリポジトリは、PlatformIO を使用して ESP32 上で LED を制御するサンプルプロジェクトです。

## ディレクトリ構成

```
platformio.ini         # PlatformIO 設定ファイル
include/               # ヘッダファイル用ディレクトリ
lib/                   # ライブラリ用ディレクトリ
src/                   # ソースコード（main.cpp など）
test/                  # テストコード用ディレクトリ
```

## セットアップ

1. [PlatformIO](https://platformio.org/) をインストールしてください。
2. このリポジトリをクローンします。
3. プロジェクトディレクトリで以下のコマンドを実行してビルド・書き込みを行います。

```sh
platformio run --target upload
```

## 動作概要

- `src/main.cpp` に ESP32 で LED を制御するサンプルコードが含まれています。
- 必要に応じて `platformio.ini` でボードやライブラリの設定を変更してください。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
