# espnow_utils.py
import network, espnow

def init_espnow(channel=1):
    sta = network.WLAN(network.STA_IF)
    ap  = network.WLAN(network.AP_IF)

    ap.active(False)         # AP無効
    sta.active(True)
    sta.disconnect()         # 自動再接続防止
    sta.config(channel=channel)
    try:
        sta.config(pm=0xa11140)  # 省電力OFF（ESP32）
    except:
        pass

    e = espnow.ESPNow()
    e.active(True)
    return e, sta

def add_peer_with_channel(e, mac, channel=1):
    """
    一部の MicroPython/ESP-IDF 組合せでは、peer 登録時に channel を明示すると安定します。
    """
    try:
        e.add_peer(mac, channel=channel)
    except TypeError:
        # channel 指定未対応ビルドは引数なしで登録
        e.add_peer(mac)
