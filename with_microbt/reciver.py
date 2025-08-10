# nus_central_aioble_sub_rx.py
# aioble / 通知のみ（RX-Indicate固定）+ keepalive + 自動再接続
# 物理ボタンで LED トグル（デバウンス）
# LED 状態が変わったら micro:bit へ STATE:ON/OFF を送信（NUS UART）

import uasyncio as asyncio
import aioble, bluetooth
from machine import Pin
import utime

# ===== 設定 =====
TARGET_ADDR     = ""                    # 固定 MAC は使わない（micro:bit はリセットで変わるため）
TARGET_NAME_KEY = "BBC MICRO:BIT"       # 名前で拾う
SCAN_MS         = 20000                 # スキャン時間
IND_TIMEOUT_MS  = 5000                  # 受信待ちタイムアウト（切断はしない）
KEEPALIVE_MS    = 10000                 # 10 秒ごとに "ESP?\n" を送る
SHOW_ADV_LOG    = False                 # True で広告ログ表示

# NUS UUID
UUID_NUS = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UUID_RX  = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")  # ← Indicate を購読
UUID_TX  = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")  # ← Write(中央→micro:bit)

# ===== LED =====
LED = Pin(19, Pin.OUT)
LED.off()

# ===== ボタン設定（デバウンス対応）=====
# 例: ESP32 の BOOT ボタンは GPIO0。内部プルアップ & 押下で GND（アクティブ Low）
BUTTON_PIN        = 0
BUTTON_ACTIVE_LOW = True
DEBOUNCE_MS       = 30      # チャタリング吸収しきい値
BUTTON_POLL_MS    = 5       # ポーリング周期

if BUTTON_ACTIVE_LOW:
    BTN = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    def _is_pressed():
        return BTN.value() == 0
else:
    BTN = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
    def _is_pressed():
        return BTN.value() == 1

# ===== 接続中にだけ使う TX キャラクタリスティック参照 =====
CURRENT_TX = None

def _state_text():
    return b"STATE:ON\n" if LED.value() else b"STATE:OFF\n"

async def _send_state_once():
    """接続中なら一度だけ STATE を送る（失敗はログのみ。再接続で回復）"""
    tx = CURRENT_TX
    if not tx:
        return
    msg = _state_text()
    try:
        try:
            await tx.write(msg)          # 新しめ aioble
        except TypeError:
            await tx.write(msg, False)   # 旧 aioble: False = Write No Response
        print("TX:", msg.decode().rstrip())
    except Exception as e:
        print("TX failed:", e)

def notify_led_state():
    """await できない場所から送信用タスクを起動"""
    try:
        asyncio.create_task(_send_state_once())
    except AttributeError:
        # 古い uasyncio 互換
        loop = asyncio.get_event_loop()
        loop.create_task(_send_state_once())

# ===== ヘルパ =====
def _mac(b): return ":".join("%02x" % x for x in b).lower()

def _dev_mac(dev):
    if hasattr(dev, "addr"):
        try: return _mac(dev.addr)
        except: pass
    for a in ("address", "addr"):
        f = getattr(dev, a, None)
        if callable(f):
            try: return _mac(f())
            except: pass
    return "?"

def _handle_text(s):
    """micro:bit → 中央（本機）へのコマンドを解釈して LED を制御"""
    before = LED.value()
    m = s.strip().upper()
    if m in ("1", "ON"):
        LED.on();  changed = (before != 1); print("LED ON")
    elif m in ("0", "OFF"):
        LED.off(); changed = (before != 0); print("LED OFF")
    elif m == "TOGGLE":
        LED.value(1-LED.value()); changed = True; print("LED TOGGLE")
    else:
        changed = False

    # 変化があったら micro:bit へ現在状態を通知
    if changed:
        notify_led_state()

# ===== スキャン =====
async def scan_for_target():
    print("Scanning...")
    target = None
    async with aioble.scan(SCAN_MS, interval_us=30000, window_us=30000, active=True) as scanner:
        async for res in scanner:
            dev = getattr(res, "device", None) or res
            name = ""
            try: name = res.name() or ""
            except: pass
            mac = _dev_mac(dev)
            if SHOW_ADV_LOG:
                try: rssi = res.rssi
                except: rssi = "?"
                print("ADV:", mac, "RSSI:", rssi, "NAME:", name)
            if (TARGET_ADDR and mac == TARGET_ADDR) or (TARGET_NAME_KEY in name.upper()):
                target = dev
                break
    return target

# ===== NUS 特性探索（aioble の版差に対応）=====
async def discover_chars(conn):
    # 新 API
    try:
        svc = await aioble.Service.discover(conn, UUID_NUS)
        rx  = await aioble.Characteristic.discover(conn, svc, UUID_RX)
        tx  = await aioble.Characteristic.discover(conn, svc, UUID_TX)
        return rx, tx
    except Exception as e1:
        # 旧 API
        try:
            svc = await conn.service(UUID_NUS)
            rx  = await svc.characteristic(UUID_RX)
            tx  = await svc.characteristic(UUID_TX)
            return rx, tx
        except Exception as e2:
            print("Discover failed:", e1, "/", e2)
            return None, None

# ===== Keepalive（ESP? 送信）=====
async def keepalive(tx_char, last_ka_ms):
    if not tx_char: return utime.ticks_ms()
    if utime.ticks_diff(utime.ticks_ms(), last_ka_ms) >= KEEPALIVE_MS:
        try:
            try:
                await tx_char.write(b"ESP?\n")       # 新しめ aioble
            except TypeError:
                await tx_char.write(b"ESP?\n", False) # 旧 aioble
            print("KA -> mb")
        except Exception:
            # 送信失敗はここでは無視（上位で切断検知）
            pass
        return utime.ticks_ms()
    return last_ka_ms

# ===== 受信ループ（通知のみ）=====
async def recv_loop(conn, rx_char, tx_char):
    last_ka = utime.ticks_ms()
    while True:
        # Indicate を待つ（タイムアウトしたら keepalive だけ送る）
        try:
            data = await rx_char.indicated(timeout_ms=IND_TIMEOUT_MS)
            if data:
                try: txt = data.decode().rstrip()
                except: txt = str(data)
                print("RX:", txt)
                _handle_text(txt)
        except Exception as e:
            # 接続喪失の判定
            try:
                is_conn = False
                if hasattr(conn, "is_connected"):
                    is_conn = conn.is_connected()
                elif hasattr(conn, "connected"):
                    is_conn = bool(conn.connected)
                if not is_conn:
                    print("Link lost. Reconnect...")
                    raise
                # errno からも切断っぽさを推定
                if isinstance(e, OSError) and e.args and isinstance(e.args[0], int) and e.args[0] in (19, 113, 116, 128):
                    print("Link error", e.args[0], "-> Reconnect...")
                    raise
            except:
                raise
            # 一時エラーは小休止して継続
            await asyncio.sleep_ms(50)

        # keepalive（失敗したら上位で再接続へ）
        try:
            last_ka = await keepalive(tx_char, last_ka)
        except Exception:
            print("Keepalive failed -> Reconnect...")
            raise

# ===== 1 セッション =====
async def run_once():
    dev = await scan_for_target()
    if not dev:
        print("micro:bit not found. Retry.")
        return

    mac = _dev_mac(dev)
    print("Connecting to", mac, "...")
    try:
        conn = await dev.connect(timeout_ms=6000)
    except Exception as e:
        print("Connect failed:", e)
        return

    try:
        # MTU 交換（対応していれば）
        try: await conn.exchange_mtu()
        except: pass

        rx_char, tx_char = await discover_chars(conn)
        if not rx_char:
            print("No RX char. Disconnect.")
            await conn.disconnect()
            return

        # RX(0x6E400002) を Indicate で購読
        try:
            await rx_char.subscribe(indicate=True)
            print("Subscribed RX via INDICATE")
        except Exception as e:
            print("Subscribe failed:", e)
            await conn.disconnect()
            return

        # TX を保持（接続中のみ有効）
        global CURRENT_TX
        CURRENT_TX = tx_char

        # 軽プローブ
        await keepalive(tx_char, utime.ticks_ms() - KEEPALIVE_MS)

        # 接続直後に現在の LED 状態を通知
        notify_led_state()

        print("Waiting notifications...")
        await recv_loop(conn, rx_char, tx_char)

    except Exception as e:
        print("Session error:", e)
    finally:
        # 切断時に TX を破棄
        CURRENT_TX = None
        try: await conn.disconnect()
        except: pass
        print("Disconnected.")

# ===== 物理ボタン → LED トグル（デバウンス付き）=====
async def button_task():
    """
    状態遷移でデバウンス:
      - 押下エッジ検出
      - DEBOUNCE_MS 継続で確定押下
      - LED をトグル & 状態通知
      - 離すまで待機（離し側もデバウンス）
    """
    while True:
        # 押下待ち
        while not _is_pressed():
            await asyncio.sleep_ms(BUTTON_POLL_MS)

        t0 = utime.ticks_ms()
        # 一定時間連続して押されていたら確定
        while _is_pressed() and utime.ticks_diff(utime.ticks_ms(), t0) < DEBOUNCE_MS:
            await asyncio.sleep_ms(BUTTON_POLL_MS)

        if _is_pressed():  # 安定押下
            # トグル & 状態通知
            LED.value(1 - LED.value())
            print("BTN: TOGGLE ->", "ON" if LED.value() else "OFF")
            notify_led_state()

            # 離すまで待機
            while _is_pressed():
                await asyncio.sleep_ms(BUTTON_POLL_MS)
            t1 = utime.ticks_ms()
            # 離し側デバウンス
            while (not _is_pressed()) and utime.ticks_diff(utime.ticks_ms(), t1) < DEBOUNCE_MS:
                await asyncio.sleep_ms(BUTTON_POLL_MS)

        await asyncio.sleep_ms(BUTTON_POLL_MS)

# ===== メインループ（自動再接続 + ボタン監視）=====
async def main():
    # 物理ボタン監視タスク
    try:
        asyncio.create_task(button_task())
    except AttributeError:
        # 古い uasyncio 互換
        loop = asyncio.get_event_loop()
        loop.create_task(button_task())

    # BLE セッションを回し続ける
    while True:
        await run_once()
        await asyncio.sleep_ms(800)

asyncio.run(main())
