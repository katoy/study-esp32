# espnow_common.py
import network, espnow

# 推奨チャネル（1/6/11 のいずれか）。sender/receiver で必ず同じ値に！
CHANNEL = 6
# ブロードキャスト MAC
BCAST = b'\xff\xff\xff\xff\xff\xff'

# コマンド/状態メッセージ
CMD_TOGGLE = b"toggle"
CMD_ON = b"on"
CMD_OFF = b"off"
CMD_STATE_REQ = b"ESP?"
STATE_ON = b"STATE:ON"
STATE_OFF = b"STATE:OFF"

def init_espnow(channel: int = CHANNEL):
    """
    AP無効 / STA有効 / 省電力OFF / チャネル固定 → ESP-NOW 有効化
    戻り値: (espnow_obj, sta_iface)
    """
    sta = network.WLAN(network.STA_IF)
    ap  = network.WLAN(network.AP_IF)

    ap.active(False)
    sta.active(True)
    sta.disconnect()
    sta.config(channel=channel)
    try:
        # 省電力OFF（ビルドにより無視される場合あり）
        sta.config(pm=0xa11140)
    except:
        pass

    e = espnow.ESPNow()
    e.active(True)
    return e, sta

def add_broadcast_peer(e, channel: int = CHANNEL):
    """
    ブロードキャスト宛も peer 登録が必要。実装差を吸収して channel 指定を試みる。
    """
    try:
        e.add_peer(BCAST, channel=channel)
    except TypeError:
        e.add_peer(BCAST)

def recv_bytes(e, timeout_ms: int = 20):
    """
    e.recv(...) の戻りを bytes に正規化して返す。
    戻り値: (host, msg_bytes or None)
    """
    host, msg = e.recv(timeout_ms)
    if not msg:
        return host, None
    try:
        msg = bytes(msg).strip()
    except Exception:
        msg = msg.tobytes().strip() if hasattr(msg, "tobytes") else msg
    return host, msg
