# toio_motor_test.py
# BLE接続で toio のモーターを制御する最小テストプログラム
# toio_controller_aioble.py 必須

import uasyncio as asyncio
from toio_controller_aioble import ToioControllerAioble

async def main():
    print("[toio] スキャン開始（toio本体は青点滅状態で！）")
    ctrl = ToioControllerAioble(debug=True)
    try:
        connected = await ctrl.scan_and_connect(scan_ms=15000)
        print(f"[DEBUG] scan_and_connect: {connected}")
        await ctrl.discover_services()
        print("[DEBUG] discover_services完了: chars=", ctrl.chars.keys())
        # バッテリー残量取得
        battery = await ctrl.read_battery()
        print(f"[DEBUG] Battery: {battery}")
        print("[toio] 接続・サービス取得完了。LED/motor制御テスト")


        # motorキャラクタリスティック取得確認
        if ctrl.chars.get("motor") is None:
            print("[ERROR] motorキャラクタリスティック取得失敗: ctrl.chars=", ctrl.chars)
            return

        # 右回転（左輪前進/右輪後退、速度100）
        pkt = bytes([0x01, 100, 1, 100, 2, 10])
        print(f"[toio] Motor pkt: {list(pkt)} → write_motor 実行 (右回転 duration=10)")
        await ctrl.write_motor(pkt)
        await asyncio.sleep(1)

        pkt = bytes([0x01, 100, 1, 100, 2, 255])
        print(f"[toio] Motor pkt: {list(pkt)} → write_motor 実行 (右回転 duration=255)")
        await ctrl.write_motor(pkt)
        await asyncio.sleep(3)


        # 左回転（左輪後退/右輪前進、速度100）
        pkt = bytes([0x01, 1, 1, 100, 2, 2, 100])
        print(f"[toio] Motor pkt: {list(pkt)} → write_motor 実行 (左回転 duration=10)")
        await ctrl.write_motor(pkt)
        await asyncio.sleep(1)

        pkt = bytes([0x01, 1, 2, 100, 2, 1, 100])
        print(f"[toio] Motor pkt: {list(pkt)} → write_motor 実行 (左回転 duration=255)")
        await ctrl.write_motor(pkt)
        await asyncio.sleep(3)


        # 停止（2秒）
        pkt = bytes([0x01, 1, 1, 0, 2, 1, 0])
        print(f"[toio] Motor pkt: {list(pkt)} → write_motor 実行")
        await ctrl.write_motor(pkt)
        await asyncio.sleep(1)

        print("[toio] テスト完了")
    except Exception as e:
        print("[ERROR] Motor制御例外:", repr(e))

asyncio.run(main())
