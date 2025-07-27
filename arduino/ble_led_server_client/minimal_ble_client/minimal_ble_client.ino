#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <BLEClient.h>
#include <BLEUtils.h>

// サーバー側と同じ定義
const char   DEVICE_NAME[]         = "MINI_SERVER_NAME";
constexpr uint16_t MANUFACTURER_ID  = 0xFFFF;

String        serverAddrStr;
bool          shouldConnect     = false;
bool          connectedFlag     = false;
BLEClient*    client            = nullptr;
BLEScan*      scanner           = nullptr;

// スキャン開始
void startScan() {
  Serial.println("Client: >>> start scan (5s)");
  scanner->start(5, false);
}

// 検出コールバック
class ScanCB : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice adv) override {
    if (adv.haveName() && adv.getName().equals(DEVICE_NAME)) {
      Serial.println("Client: Found by name");
      serverAddrStr = adv.getAddress().toString();
      shouldConnect = true;
      scanner->stop();
      return;
    }
    if (adv.haveManufacturerData()) {
      String md = adv.getManufacturerData();
      if (md.length() >= 2) {
        uint16_t id = ((uint8_t)md[1] << 8) | (uint8_t)md[0];
        if (id == MANUFACTURER_ID) {
          Serial.println("Client: Found by manufacturer data");
          serverAddrStr = adv.getAddress().toString();
          shouldConnect = true;
          scanner->stop();
          return;
        }
      }
    }
  }
};

// 接続コールバック
class ClientCB : public BLEClientCallbacks {
  void onConnect(BLEClient*) override {
    Serial.println("Client: connected");
    connectedFlag = true;
  }
  void onDisconnect(BLEClient*) override {
    Serial.println("Client: disconnected → will rescan");
    connectedFlag = false;
    shouldConnect = false;
  }
};

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  Serial.println("Client: init");

  BLEDevice::init("");
  scanner = BLEDevice::getScan();
  scanner->setAdvertisedDeviceCallbacks(new ScanCB());
  scanner->setActiveScan(true);
  scanner->setInterval(100);
  scanner->setWindow(50);
}

void loop() {
  if (!connectedFlag) {
    if (shouldConnect) {
      Serial.print("Client: connecting to ");
      Serial.println(serverAddrStr);
      BLEAddress addr(serverAddrStr);
      client = BLEDevice::createClient();
      client->setClientCallbacks(new ClientCB());
      // 変更後（2秒でタイムアウトさせる例）
      const uint32_t CONNECT_TIMEOUT_MS = 2000;
      if (!client->connect(addr, BLE_ADDR_TYPE_PUBLIC, CONNECT_TIMEOUT_MS)) {
        Serial.println("Client: connect NG (timeout) → retry scan");
        shouldConnect = false;
      }
    } else {
      startScan();
      BLEScanResults* res = scanner->start(5, false);
      Serial.printf("Client: scan done, %d devices seen\n", res->getCount());
      scanner->clearResults();
    }
  }
  delay(500);
}
