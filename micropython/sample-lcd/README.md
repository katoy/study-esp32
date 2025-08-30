# NTP時計（ESP32 + MicroPython + LCD）

このプロジェクトは、ESP32マイコンとMicroPythonを使い、LCDディスプレイにNTPサーバーから取得した時刻を表示するサンプルです。

## 構成
- ESP32開発ボード
- LCDディスプレイ（例：I2C接続の16x2 LCD）
- MicroPythonファームウェア
- サンプルスクリプト：`ntp-clock.py`

## 配線方法
### LCD（I2C接続）の例
| LCDピン | ESP32ピン |
|---------|-----------|
| VCC     | 3.3V/5V   |
| GND     | GND       |
| SDA     | GPIO21    |
| SCL     | GPIO22    |

※ SDA/SCLピンはESP32のI2C標準ピンですが、他のピンも利用可能です。`ntp-clock.py`内の設定に合わせてください。

## ライブラリー準備
1. MicroPythonファームウェアをESP32に書き込みます。
   - [公式手順](https://micropython.org/download/esp32/)
2. 必要なMicroPythonライブラリーをインストールします。
   - I2C LCD用ライブラリー（例：`lcd_api.py`, `i2c_lcd.py`）
   - これらは[MicroPython-ESP8266-LCD](https://github.com/dhylands/python_lcd)などから取得できます。
   - ファイルをESP32にアップロードするには、`ampy`や`rshell`、Thonnyなどを利用してください。

## サンプルスクリプトの使い方
1. `ntp-clock.py`をESP32にアップロードします。
2. `config.py` にWi-FiのSSIDとパスワードを記載してください。
   ```python
   AP_CONFIG = {
      'ssid': 'ご自身のSSID',
      'password': 'ご自身のパスワード'
   }
   ```
3. LCDのI2Cアドレスやピン番号は `ntp-clock.py` 内で調整できます。
4. ESP32を起動すると、LCDに日本時間（yyyy-mm-dd形式）でNTPサーバーから取得した時刻が表示されます。
5. LCDのカーソルは自動的に消去されます。

## 注意事項
- Wi-Fi設定（SSID/PASSWORD）は `config.py` で管理してください（`.gitignore`で除外済み）。
- NTPサーバーへの接続にはインターネット環境が必要です。
- LCDの種類や接続方法によっては、ライブラリーや配線が異なる場合があります。
- LCDのI2Cアドレスは実機のスキャン結果に合わせてください。


## 参考リンク
- [MicroPython公式](https://micropython.org/)
- [python_lcdライブラリー](https://github.com/dhylands/python_lcd)
- [ESP32 MicroPython入門](https://docs.micropython.org/en/latest/esp32/quickref.html)

---
ご質問や不明点があれば、Issueやコメントでご連絡ください。
