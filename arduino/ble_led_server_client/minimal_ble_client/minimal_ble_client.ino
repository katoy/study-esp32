// minimal_ble_client_final.ino
#include <BLEDevice.h>

constexpr char    TARGET_NAME[]         = "MINI_SERVER_NAME";
constexpr uint16_t MANUFACTURER_ID      = 0xFFFF;
constexpr char    MANUFACTURER_STRING[] = "MINI_TEST";
// Company ID(2) + 文字列長
constexpr int     EXPECTED_MD_LEN       = 2 + sizeof(MANUFACTURER_STRING) - 1;

class MyCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) override {
    // 1) メーカー⽤データで検出
    if (advertisedDevice.haveManufacturerData()) {
      String md = advertisedDevice.getManufacturerData();
      if (md.length() == EXPECTED_MD_LEN
          && uint8_t(md.charAt(0)) == (MANUFACTURER_ID & 0xFF)
          && uint8_t(md.charAt(1)) == (MANUFACTURER_ID >> 8)
          && md.substring(2) == MANUFACTURER_STRING) {
        Serial.println("=== MINI SERVER FOUND by Manufacturer Data ===");
        BLEScan* scan = BLEDevice::getScan();
        scan->stop();
        scan->clearResults();
        return;
      }
    }

    // 2) 名前で検出（Scan Response にも対応）
    if (advertisedDevice.haveName()
        && advertisedDevice.getName() == TARGET_NAME) {
      Serial.println("=== MINI SERVER FOUND by Name ===");
      BLEScan* scan = BLEDevice::getScan();
      scan->stop();
      scan->clearResults();
      return;
    }
  }
};

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE Client...");

  BLEDevice::init("");
  BLEScan* pScan = BLEDevice::getScan();
  pScan->setAdvertisedDeviceCallbacks(new MyCallbacks());
  pScan->setActiveScan(true);
  pScan->start(0, false);  // 0秒＝見つかるまでスキャンを継続

  Serial.println("Scanning for MINI_SERVER_NAME...");
}

void loop() {
  delay(1000);
}
