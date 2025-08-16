# ESP32 MicroPython LED コントロール (AP + REST + 物理ボタン)

ESP32 上で MicroPython を用いて、以下を実現する最小構成のサンプルです。

- ESP32 自身を SoftAP 化 (任意の SSID / パスワード)
- 単一 GPIO (既定: GPIO19) に接続した LED の ON / OFF / TOGGLE 制御
- シンプルな REST API (`/api/led`) による状態取得 & 操作 (GET / POST)
- 物理ボタン (既定: GPIO0 / BOOT ボタン) 押下で LED トグル (割り込み + デバウンス)
- Web UI ( `index.html` + `style.css` ) による操作 & 1 秒毎の自動状態更新
- LED の状態は常に実際のピン値を参照 (冗長な `led_state` 変数なし)

---
## ファイル構成

| ファイル | 役割 |
|----------|------|
| `server.py` | AP 起動 / ソケットベース簡易 HTTP / REST ルータ / LED & ボタン制御 |
| `index.html` | 初期表示用 HTML テンプレート (プレースホルダ `{{PIN}}`, `{{STATE_CLASS}}`, `{{STATE_TEXT}}`) |
| `style.css` | UI スタイル (レスポンシブ / ダークモード対応) |
| `README.md` | 本ドキュメント |

---
## ハードウェア要件 / 配線

| 機能 | GPIO | 備考 |
|------|------|------|
| LED | GPIO19 (既定) | 必要に応じ変更可。`LED_ACTIVE_LOW` = True でアクティブ Low 対応 |
| ボタン (トグル) | GPIO0 | ESP32 DevKit の BOOT ボタンを利用可能 (内部 PULL_UP 利用) |

LED を 3.3V ロジックで直接点灯可能な抵抗付き LED に接続してください (例: LED アノードを GPIO19、カソードを GND 経由で抵抗)。
アクティブ Low の LED モジュールを使う場合は `server.py` の `LED_ACTIVE_LOW = True` に変更します。

---
## セットアップ手順

1. MicroPython ファームウェアを書き込んだ ESP32 を用意
2. このディレクトリの `server.py`, `index.html`, `style.css` を `ampy`, `mpremote` などで ESP32 へ転送
3. REPL で `server.py` を実行 (または `main.py` にリネームして自動起動)
4. PC / スマホで SSID: `MyESP32AP` (デフォルト) に接続 (パスワード: `password123`)
5. ブラウザで `http://192.168.4.1/` にアクセス

SSID / パスワード / IP は `server.py` 冒頭の定数で変更可能です。

---
## REST API 仕様

ベース URL: `http://192.168.4.1`

### 状態取得
```
GET /api/led
レスポンス例: {"led": "on"}
```

### 状態変更 (クエリで指示)
```
POST /api/led?state=on
POST /api/led?state=off
POST /api/led?state=toggle
```
(簡易互換で `GET /api/led?state=on|off|toggle` も許容)

レスポンス (共通):
```
{"led": "on" | "off"}
```

### 旧パス互換
`/led/on` 等の旧式パスはリダイレクトで廃止済み。古いブックマーク対応のためリダイレクト HTML を返します。

---
## Web UI

- 初回ロード時にテンプレートのプレースホルダが LED 状態で置換され提供
- 1 秒毎に `fetch('/api/led')` でポーリングし物理ボタン操作を反映
- ボタン操作 (ON / OFF / TOGGLE) は `POST /api/led?state=...` を発行し即時 `poll()` 実行
- 状態テキスト色: ON=緑系 / OFF=赤系 (ダークモード時は別配色)

---
## 実装メモ

- HTTP は低レベルソケットで最小限実装 (ヘッダ終端 `\r\n\r\n` まで読込)
- `Content-Length` 明示 + `Connection: close` で簡易化
- テンプレートは初回ロード後メモリにキャッシュ
- LED 状態は常に `machine.Pin` の値から算出 (同期ズレ防止)
- ボタン割り込みは Falling Edge + デバウンス (`DEBOUNCE_MS` 調整可能)
- 微小遅延 (`time.sleep_ms(15)`) を accept 後に入れ、初回クリック時の送信遅延を緩和

---
## カスタマイズ

| 項目 | 方法 |
|------|------|
| LED ピン変更 | `LED_PIN` を編集 |
| アクティブ Low | `LED_ACTIVE_LOW = True` |
| ボタンピン変更 | `BUTTON_PIN` を変更 (PULL_UP 想定) |
| デバウンス時間 | `DEBOUNCE_MS` を ms 単位で調整 |
| ポーリング間隔 | `index.html` 内 `setInterval(poll, 1000)` を変更 |
| SSID / パス | `SSID`, `PASSWORD` を編集 |
| IP 設定 | `IP_ADDR`, `SUBNET`, `GATEWAY`, `DNS` |

---
## トラブルシュート

| 症状 | 対処 |
|------|------|
| ページが真っ白 | 転送漏れ (特に `index.html`) を確認 / REPL ログの例外確認 |
| LED が逆論理 | `LED_ACTIVE_LOW` を True に変更 |
| ボタンが効かない | GND 配線確認 / `BUTTON_PIN` 定義確認 |
| 反応が遅い | ポーリング間隔短縮 (例: 500ms) ただしトラフィック増加に注意 |
| 旧 /led/on 等へアクセス | 自動リダイレクトされる (UI からは使用しない) |

---
## 今後の拡張アイデア

- WebSocket / Server-Sent Events でポーリング削減
- 複数 GPIO の一覧制御 / JSON 配列化
- 認証 (簡易トークン / パスワード強化)
- SPIFFS / LittleFS からの静的ファイル提供最適化
- 低電力モード対応
- OTA 更新仕組み

---
## ライセンス

このサンプルは学習用途向けで、パブリックドメイン相当 (制限なし) とします。

