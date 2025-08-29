# toio_led_blink_test.py
# toio本体のLEDを1秒ごとにON/OFF点滅させるテストスクリプト
# 必要: toio_controller_aioble.py, aioble, bluetooth, uasyncio

import uasyncio as asyncio
from toio_controller_aioble import ToioControllerAioble

async def main():
    print("[toio_test] スキャン開始（toio本体は青点滅状態で！）")
    ctrl = ToioControllerAioble(debug=True)
    await ctrl.scan_and_connect(scan_ms=15000)  # スキャン時間長め
    await ctrl.discover_services()
    print("[toio_test] 接続・サービス取得完了。LED点滅開始")
    while True:
        print("[toio_test] LED ON")
        await ctrl.led_on(ms=1000, r=0, g=255, b=0)  # 緑色1秒ON
        await asyncio.sleep(1)
        print("[toio_test] LED OFF")
        await ctrl.led_off()
        await asyncio.sleep(1)

asyncio.run(main())
