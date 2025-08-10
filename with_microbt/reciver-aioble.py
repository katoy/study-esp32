# nus_central_aioble_sub_rx.py — aioble / 通知のみ（RX-Indicate固定）+ keepalive + 自動再接続
import uasyncio as asyncio
import aioble, bluetooth
from machine import Pin
import utime

# ===== 設定 =====
TARGET_ADDR     = ""                    # 固定MACは使わない（micro:bitはリセットで変わるため）
TARGET_NAME_KEY = "BBC MICRO:BIT"       # 名前で拾う
SCAN_MS         = 20000                 # スキャン時間
IND_TIMEOUT_MS  = 5000                  # 受信待ちタイムアウト（切断はしない）
KEEPALIVE_MS    = 10000                 # 10秒ごとに "ESP?\n" を送る
SHOW_ADV_LOG    = False                 # True にすると広告ログを表示

# NUS UUID
UUID_NUS = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UUID_RX  = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")  # ← 購読（Indicate）
UUID_TX  = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")  # ← 書き込み（ESP? など）

# LED
LED = Pin(19, Pin.OUT)
LED.off()

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
    m = s.strip().upper()
    if m in ("1", "ON"):
        LED.on();  print("LED ON")
    elif m in ("0", "OFF"):
        LED.off(); print("LED OFF")
    elif m == "TOGGLE":
        LED.value(1-LED.value()); print("LED TOGGLE")

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

# ===== NUS特性探索（aiobleの版差に対応）=====
async def discover_chars(conn):
    # 新API
    try:
        svc = await aioble.Service.discover(conn, UUID_NUS)
        rx  = await aioble.Characteristic.discover(conn, svc, UUID_RX)
        tx  = await aioble.Characteristic.discover(conn, svc, UUID_TX)
        return rx, tx
    except Exception as e1:
        # 旧API
        try:
            svc = await conn.service(UUID_NUS)
            rx  = await svc.characteristic(UUID_RX)
            tx  = await svc.characteristic(UUID_TX)
            return rx, tx
        except Exception as e2:
            print("Discover failed:", e1, "/", e2)
            return None, None

# ===== Keepalive（ESP?送信）=====
async def keepalive(tx_char, last_ka_ms):
    if not tx_char: return utime.ticks_ms()
    if utime.ticks_diff(utime.ticks_ms(), last_ka_ms) >= KEEPALIVE_MS:
        try:
            try:
                await tx_char.write(b"ESP?\n")       # 新しめ aioble
            except TypeError:
                await tx_char.write(b"ESP?\n", False) # 旧 aioble: False=Write No Resp
            print("KA -> mb")
        except Exception:
            # 送れなくてもここでは切断しない（上位で検知）
            pass
        return utime.ticks_ms()
    return last_ka_ms

# ===== 受信ループ（通知のみ）=====
async def recv_loop(conn, rx_char, tx_char):
    last_ka = utime.ticks_ms()
    while True:
        # Indicateを待つ（来なければkeepaliveだけ行う）
        try:
            data = await rx_char.indicated(timeout_ms=IND_TIMEOUT_MS)
            if data:
                try: txt = data.decode().rstrip()
                except: txt = str(data)
                print("RX:", txt)
                _handle_text(txt)
        except Exception as e:
            # 接続喪失なら上位へ投げて再接続へ
            try:
                is_conn = False
                if hasattr(conn, "is_connected"):
                    is_conn = conn.is_connected()
                elif hasattr(conn, "connected"):
                    is_conn = bool(conn.connected)
                if not is_conn:
                    print("Link lost. Reconnect...")
                    raise
                # errno でも切断を検出
                if isinstance(e, OSError) and e.args and isinstance(e.args[0], int) and e.args[0] in (19, 113, 116, 128):
                    print("Link error", e.args[0], "-> Reconnect...")
                    raise
            except:
                raise
            # 一時エラーは軽く待って継続
            await asyncio.sleep_ms(50)

        # keepalive（失敗したら上位で再接続へ）
        try:
            last_ka = await keepalive(tx_char, last_ka)
        except Exception:
            print("Keepalive failed -> Reconnect...")
            raise

# ===== 1セッション =====
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
        # MTU交換（あるなら）
        try: await conn.exchange_mtu()
        except: pass

        rx_char, tx_char = await discover_chars(conn)
        if not rx_char:
            print("No RX char. Disconnect.")
            await conn.disconnect()
            return

        # RX(0x6E400002) を Indicate で購読（固定）
        try:
            await rx_char.subscribe(indicate=True)
            print("Subscribed RX via INDICATE")
        except Exception as e:
            print("Subscribe failed:", e)
            await conn.disconnect()
            return

        # 起動直後に軽プローブ（任意）
        await keepalive(tx_char, utime.ticks_ms() - KEEPALIVE_MS)

        print("Waiting notifications...")
        await recv_loop(conn, rx_char, tx_char)

    except Exception as e:
        print("Session error:", e)
    finally:
        try: await conn.disconnect()
        except: pass
        print("Disconnected.")

# ===== メインループ（自動再接続）=====
async def main():
    while True:
        await run_once()
        await asyncio.sleep_ms(800)

asyncio.run(main())
