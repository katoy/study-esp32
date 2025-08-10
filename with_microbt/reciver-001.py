# us_central_sync.py (subscribe + polling fallback)
from micropython import const
import bluetooth, time
from machine import Pin

# IRQ codes
_IRQ_SCAN_RESULT=const(5); _IRQ_SCAN_DONE=const(6)
_IRQ_PERIPHERAL_CONNECT=const(7); _IRQ_PERIPHERAL_DISCONNECT=const(8)
_IRQ_GATTC_SERVICE_RESULT=const(9); _IRQ_GATTC_SERVICE_DONE=const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT=const(11); _IRQ_GATTC_CHARACTERISTIC_DONE=const(12)
_IRQ_GATTC_READ_RESULT=const(15); _IRQ_GATTC_READ_DONE=const(16)
_IRQ_GATTC_WRITE_DONE=const(17); _IRQ_GATTC_NOTIFY=const(18); _IRQ_GATTC_INDICATE=const(20)

# Props
PROP_WRITE_NO_RESP=0x04; PROP_WRITE=0x08; PROP_NOTIFY=0x10; PROP_INDICATE=0x20

# UUIDs (NUS)
UUID_NUS=bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UUID_TX =bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")  # Write側
UUID_RX =bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")  # Indicate側
NUS_UUID128_LE=bytes.fromhex("9ECADC240EE5A9E093F3A3B50100406E")

# Scan/target
TARGET_NAME_KEY="BBC MICRO:BIT"
TARGET_ADDR_STR="c8:9c:3a:28:77:ab"
MIN_RSSI=-85
SCAN_ACTIVE=False

LED=Pin(19, Pin.OUT); LED.off()

def addr_to_str(a): return ":".join("%02x"%b for b in a).lower()

def name_from_adv(adv):
    i=0
    while i+1<len(adv):
        ln=adv[i]; i2=i+1+ln
        if ln==0: break
        t=adv[i+1]; v=adv[i+2:i2]
        if t in (0x08,0x09):
            try: return v.decode()
            except: return ""
        i=i2
    return ""

def adv_has_uuid128(adv,uuid_le):
    i=0
    while i+1<len(adv):
        ln=adv[i]; i2=i+1+ln
        if ln==0: break
        t=adv[i+1]; v=adv[i+2:i2]
        if t in (0x06,0x07):
            for j in range(0,len(v),16):
                if v[j:j+16]==uuid_le: return True
        i=i2
    return False

class Central:
    def __init__(self):
        self.ble=bluetooth.BLE(); self.ble.active(True); self.ble.irq(self._irq)
        self.reset()

    def reset(self):
        self.conn=None; self.target=None; self.svc_range=None
        self.tx_handle=None; self.tx_props=0
        self.rx_handle=None; self.rx_props=0
        self._scan_done=False; self._svc_done=False; self._char_done=False
        self._last_write=None
        self._read_buf=None; self._read_done=False
        self._last_seen=b""   # ポーリング用の直近値

    # ---- IRQ ----
    def _irq(self, event, data):
        if event==_IRQ_SCAN_RESULT:
            at,addr,adv_type,rssi,adv=data
            name=name_from_adv(adv) or ""
            want=((TARGET_ADDR_STR and addr_to_str(addr)==TARGET_ADDR_STR)
                  or (TARGET_NAME_KEY in name.upper())
                  or adv_has_uuid128(adv,NUS_UUID128_LE))
            if want and rssi>=MIN_RSSI:
                self.target=(at,bytes(addr)); self.ble.gap_scan(None)
        elif event==_IRQ_SCAN_DONE:
            self._scan_done=True
        elif event==_IRQ_PERIPHERAL_CONNECT:
            self.conn=data[0]; print("Connected.")
        elif event==_IRQ_PERIPHERAL_DISCONNECT:
            print("Disconnected."); self.reset(); time.sleep_ms(1200)
        elif event==_IRQ_GATTC_SERVICE_RESULT:
            ch,start,end,uuid=data
            if ch==self.conn and uuid==UUID_NUS: self.svc_range=(start,end)
        elif event==_IRQ_GATTC_SERVICE_DONE:
            self._svc_done=True
        elif event==_IRQ_GATTC_CHARACTERISTIC_RESULT:
            ch,_,val_handle,props,uuid=data
            if ch==self.conn and self.svc_range:
                if uuid==UUID_TX: self.tx_handle=val_handle; self.tx_props=props
                elif uuid==UUID_RX: self.rx_handle=val_handle; self.rx_props=props
        elif event==_IRQ_GATTC_CHARACTERISTIC_DONE:
            self._char_done=True
        elif event==_IRQ_GATTC_WRITE_DONE:
            ch,h,status=data
            if ch==self.conn:
                self._last_write=(h,status)
                print("WRITE_DONE handle:", h, "status:", status)
        elif event==_IRQ_GATTC_READ_RESULT:
            ch,h,value=data
            if ch==self.conn:
                self._read_buf=bytes(value)
        elif event==_IRQ_GATTC_READ_DONE:
            ch,h,status=data
            if ch==self.conn:
                self._read_done=True
        elif event in (_IRQ_GATTC_NOTIFY,_IRQ_GATTC_INDICATE):
            ch,val_handle,payload=data
            if ch==self.conn and val_handle==self.rx_handle:
                try: msg=payload.decode().rstrip()
                except: msg=str(payload)
                self._handle_msg("IND", msg)

    # ---- helpers ----
    def _wait(self,cond,to_ms):
        t0=time.ticks_ms()
        while not cond():
            if time.ticks_diff(time.ticks_ms(),t0)>to_ms: return False
            time.sleep_ms(20)
        return True

    def _handle_msg(self, src, msg):
        print("RX(%s): %s" % (src, msg))
        m=msg.strip().upper()
        if m in ("1","ON"): LED.on();  print("LED ON")
        elif m in ("0","OFF"): LED.off(); print("LED OFF")
        elif m=="TOGGLE": LED.value(1-LED.value()); print("LED TOGGLE")

    def _read_once(self, h, timeout_ms=500):
        """sync read with small timeout"""
        try:
            self._read_buf=None; self._read_done=False
            self.ble.gattc_read(self.conn, h)
            t0=time.ticks_ms()
            while (not self._read_done) and time.ticks_diff(time.ticks_ms(),t0)<timeout_ms:
                time.sleep_ms(10)
            return self._read_buf
        except:
            return None

    def _connected(self): return self.conn is not None

    # ---- main ----
    def run(self):
        while True:
            print("Scanning (12s, passive)...")
            self._scan_done=False; self.target=None
            self.ble.gap_scan(12000,30000,30000,SCAN_ACTIVE)
            self._wait(lambda: self._scan_done,14000)
            if not self.target: print("micro:bit not found. Retry."); continue

            at,addr=self.target
            print("Connecting to", addr_to_str(addr), "...")
            self.ble.gap_connect(at, addr)
            if not self._wait(self._connected,8000): print("Connect timeout."); continue
            time.sleep_ms(800)
            if not self._connected(): print("Disconnected before GATT. Retry."); continue

            print("Discovering services...")
            self._svc_done=False
            try: self.ble.gattc_discover_services(self.conn,UUID_NUS)
            except: self.ble.gattc_discover_services(self.conn)
            if (not self._wait(lambda: self._svc_done or not self._connected(),5000)) or (not self._connected()) or (not self.svc_range):
                print("NUS not found or disconnected. Retry.")
                if self._connected(): self.ble.gap_disconnect(self.conn); time.sleep_ms(200)
                continue

            start,end=self.svc_range
            print("Discovering characteristics...")
            self._char_done=False; self.tx_handle=None; self.rx_handle=None
            self.tx_props=0; self.rx_props=0
            self.ble.gattc_discover_characteristics(self.conn,start,end)
            if (not self._wait(lambda: self._char_done or not self._connected(),5000)) or (not self._connected()):
                print("Char discovery failed/disconnected.")
                if self._connected(): self.ble.gap_disconnect(self.conn); time.sleep_ms(200)
                continue
            print("tx:", self.tx_handle, "props:0x%02x"%self.tx_props, "rx:", self.rx_handle, "props:0x%02x"%self.rx_props)

            # ---- RX(Indicate) の CCCD を直接開く（+1..+3）----
            want=b"\x02\x00"  # Indicate
            ok=False
            for off in (1,2,3):
                h=self.rx_handle+off
                try:
                    self._last_write=None
                    self.ble.gattc_write(self.conn,h,want,1)
                    t0=time.ticks_ms()
                    while self._last_write is None and time.ticks_diff(time.ticks_ms(),t0)<2000:
                        time.sleep_ms(20)
                    if self._last_write and self._last_write[0]==h and self._last_write[1]==0:
                        print("CCCD opened @", h, "(for RX)")
                        ok=True; break
                except: pass
            if not ok:
                print("CCCD open failed. Retry.")
                if self._connected(): self.ble.gap_disconnect(self.conn); time.sleep_ms(300)
                continue

            print("Subscribed. Waiting notifications... (and poll fallback)")
            self._last_seen=b""
            # 受信待ち：Indicate を待ちつつ 500ms おきに read でフォールバック
            while self._connected():
                # poll read
                val=self._read_once(self.rx_handle, timeout_ms=250)
                if val and val!=self._last_seen:
                    self._last_seen=val
                    try: txt=val.decode().rstrip()
                    except: txt=str(val)
                    self._handle_msg("POLL", txt)
                time.sleep_ms(250)

Central().run()
