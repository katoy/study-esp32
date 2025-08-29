# toio_controller_aioble.py — aiobleベースのtoioコントローラ（MicroPython用）
# 機能: 接続/探索・Motor・LED・Sound・Battery・Button・Notify購読
# 依存: aioble, bluetooth（uasyncioベース）

import uasyncio as asyncio
import aioble, bluetooth

# ==== toio UUID（完全一致）====
UUID_SVC     = bluetooth.UUID("10b20100-5b3b-4571-9508-cf3efcd7bbae")
UUID_ID      = bluetooth.UUID("10b20101-5b3b-4571-9508-cf3efcd7bbae")
UUID_MOTOR   = bluetooth.UUID("10b20102-5b3b-4571-9508-cf3efcd7bbae")
UUID_LIGHT   = bluetooth.UUID("10b20103-5b3b-4571-9508-cf3efcd7bbae")
UUID_SOUND   = bluetooth.UUID("10b20104-5b3b-4571-9508-cf3efcd7bbae")
UUID_SENSOR  = bluetooth.UUID("10b20106-5b3b-4571-9508-cf3efcd7bbae")
UUID_BUTTON  = bluetooth.UUID("10b20107-5b3b-4571-9508-cf3efcd7bbae")
UUID_BATTERY = bluetooth.UUID("10b20108-5b3b-4571-9508-cf3efcd7bbae")
UUID_CONF    = bluetooth.UUID("10b201ff-5b3b-4571-9508-cf3efcd7bbae")

class ToioControllerAioble:
    async def led_off(self):
        char = self.chars.get("light")
        if char:
            pkt = bytes([0x03, 0, 0x01, 0x01, 0, 0, 0])
            await char.write(pkt)
    def __init__(self, debug=False):
        self.debug = debug
        self.device = None
        self.conn = None
        self.chars = {}

    async def scan_and_connect(self, scan_ms=8000):
        while True:
            self.device = None
            async with aioble.scan(scan_ms) as scanner:
                async for res in scanner:
                    name = res.name() or ""
                    mac = getattr(res, "address", lambda: "?")()
                    rssi = getattr(res, "rssi", "?")
                    print(f"[SCAN] name: {name}, MAC: {mac}, RSSI: {rssi}")
                    # より広い部分一致（toio, TOIO, tOio など）
                    if name and "toio" in name.lower():
                        print(f"[SCAN] toio候補: {name}, MAC: {mac}, RSSI: {rssi}")
                        self.device = res.device
                        break
                    elif name and ("cube" in name.lower() or "toio" in name.lower()):
                        print(f"[SCAN] toio/cube候補: {name}, MAC: {mac}, RSSI: {rssi}")
                        self.device = res.device
                        break
            if self.device:
                self.conn = await self.device.connect()
                print("[DEBUG] toio connected.")
                return True
            print("[DEBUG] toio not found. 再スキャンします…")

    async def discover_services(self):
        # aioble旧API対応
        try:
            svc = await self.conn.service(UUID_SVC)
            self.chars["motor"]   = await svc.characteristic(UUID_MOTOR)
            self.chars["light"]   = await svc.characteristic(UUID_LIGHT)
            self.chars["sound"]   = await svc.characteristic(UUID_SOUND)
            self.chars["button"]  = await svc.characteristic(UUID_BUTTON)
            self.chars["battery"] = await svc.characteristic(UUID_BATTERY)
            self.chars["conf"]    = await svc.characteristic(UUID_CONF)
            if self.debug:
                print("Discovered chars:", self.chars.keys())
        except Exception as e:
            print("Service/Char discover error:", e)

    async def write_motor(self, data):
        char = self.chars.get("motor")
        if char:
            await char.write(data)

    async def led_on(self, ms=0, r=0, g=0, b=0):
        char = self.chars.get("light")
        if char:
            dur = max(0, min(ms//10, 255))
            pkt = bytes([0x03, dur, 0x01, 0x01, r&0xFF, g&0xFF, b&0xFF])
            await char.write(pkt)

    async def led_blink(self, seq, repeat=0):
        char = self.chars.get("light")
        if char and seq:
            ops = min(len(seq), 29)
            pkt = bytearray([0x04, repeat&0xFF, ops])
            for (ms, r, g, b) in seq[:ops]:
                pkt += bytes([max(1, min(ms//10,255)), 0x01, 0x01, r&0xFF, g&0xFF, b&0xFF])
            await char.write(bytes(pkt))

    async def sound_effect(self, effect_id=4, volume=0xFF):
        char = self.chars.get("sound")
        if char:
            eid = max(0, min(effect_id, 255))
            vol = 0 if volume == 0 else 0xFF
            pkt = bytes([0x02, eid, vol])
            await char.write(pkt)

    async def read_battery(self):
        char = self.chars.get("battery")
        if char:
            raw = await char.read()
            if raw and len(raw) >= 2 and raw[0] == 0x01:
                return int(raw[1])
            elif raw:
                return int(raw[0])
        return None

    async def subscribe_button(self, callback):
        char = self.chars.get("button")
        if char:
            await char.subscribe(notify=True)
            while True:
                data = await char.notified()
                callback(data)

    async def disconnect(self):
        if self.conn:
            await self.conn.disconnect()
            if self.debug: print("disconnected")

# 使い方例（uasyncioで）
# async def main():
#     ctrl = ToioControllerAioble(debug=True)
#     await ctrl.scan_and_connect()
#     await ctrl.discover_services()
#     await ctrl.led_on(ms=500, r=255, g=0, b=0)
#     await ctrl.write_motor(b'...')
#     battery = await ctrl.read_battery()
#     print("Battery:", battery)
#     await ctrl.disconnect()
# asyncio.run(main())
