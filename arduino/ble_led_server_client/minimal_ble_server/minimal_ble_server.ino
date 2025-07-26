// minimal_ble_server_fixed2.ino
#include <BLEDevice.h>
#include <BLEServer.h>

constexpr char   DEVICE_NAME[]        = "MINI_SERVER_NAME";
constexpr uint16_t MANUFACTURER_ID    = 0xFFFF;
constexpr char   MANUFACTURER_STRING[] = "MINI_TEST";

// Arduino String でメーカー⽤データを組み立てる
static String makeManufacturerData() {
  // 先頭 2 バイト＋文字列長分を確保
  String md;
  md.reserve(2 + sizeof(MANUFACTURER_STRING) - 1);

  // リトルエンディアンで Company ID を追加
  md += char(MANUFACTURER_ID        & 0xFF);
  md += char((MANUFACTURER_ID >> 8) & 0xFF);

  // テキストデータを追加
  md += MANUFACTURER_STRING;
  return md;
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE Server...");

  BLEDevice::init(DEVICE_NAME);
  BLEServer*     pServer = BLEDevice::createServer();
  BLEAdvertising* pAdv    = BLEDevice::getAdvertising();

  // 広告データをまとめて設定
  BLEAdvertisementData advData;
  advData.setFlags(0x06);                             // General discoverable + BR/EDR unsupported
  advData.setManufacturerData(makeManufacturerData()); // ← Arduino String を渡す
  pAdv->setAdvertisementData(advData);

  // スキャンレスポンスには名前だけ
  BLEAdvertisementData scanRes;
  scanRes.setName(DEVICE_NAME);
  pAdv->setScanResponseData(scanRes);

  pAdv->start();
  Serial.println("Advertising started.");
}

void loop() {
  delay(2000);
}
