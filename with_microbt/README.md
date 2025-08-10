# study-esp32

このリポジトリは、ESP32およびmicro:bitを使用した学習プロジェクトです。
主にBluetooth Low Energy (BLE) 通信のテストコードが含まれています。

## ファイル構成

- `micro_bit.js`: micro:bit側で動作するJavaScriptコードです。BLE通信のペリフェラル（サーバー）側を実装している可能性があります。
- `reciver-001.py`: BLE通信のセントラル（クライアント）側として動作するPythonスクリプトです。
- `reciver-aioble.py`: Pythonの `aioble` ライブラリを使用した、非同期I/OによるBLE受信スクリプトです。

## 概要

このプロジェクトでは、micro:bitからBLEアドバタイズを発信し、それをPythonスクリプトを実行しているデバイスで受信する、といった実験を行っているものと推測されます。
