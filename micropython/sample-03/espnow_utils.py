import network
import espnow

def init_espnow():
    """
    Initializes WLAN and ESP-NOW and returns an ESPNow object.
    """
    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.disconnect()  # For ESP8266, ensures a clean state

    e = espnow.ESPNow()
    e.active(True)
    return e
 