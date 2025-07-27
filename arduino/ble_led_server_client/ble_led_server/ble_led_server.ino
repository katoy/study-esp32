// minimal_ble_server_fixed2.ino
#include <BLEDevice.h>
#include <BLEServer.h>

// Application definitions
constexpr int BOOT_BUTTON_PIN = 0;  // BOOT ボタンのピン
constexpr int LED_PIN         = 19; // LED のピン

// Global variables
bool ledState = LOW; // LED の点灯状態 (初期値: 消灯)

// Variables for button debounce
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay    = 50; // 50ms のデバウンス時間
int lastButtonState;

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

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      Serial.println("Connected");
      pServer->getAdvertising()->stop();
    }

    void onDisconnect(BLEServer* pServer) {
      Serial.println("Disconnected");
      pServer->getAdvertising()->start();
      Serial.println("Advertising restarted.");
    }
};

void setupLed() {
  // Setup pins
  pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);

  // Initialize LED state
  digitalWrite(LED_PIN, ledState);
  lastButtonState = digitalRead(BOOT_BUTTON_PIN);
}

void setupBluetooth() {
  BLEDevice::init(DEVICE_NAME);
  BLEServer*     pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
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

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE Server...");

  setupLed();
  setupBluetooth();
}

// ボタン入力を処理し、LED の状態をトグルする
void handleButton() {
  int reading = digitalRead(BOOT_BUTTON_PIN);

  // ボタンが押された瞬間 (HIGH から LOW への変化) を検出
  if (reading == LOW && lastButtonState == HIGH) {
    // 前回の処理から十分な時間が経過しているか確認 (チャタリング防止)
    if (millis() - lastDebounceTime > debounceDelay) {
      // LED の状態を反転
      ledState = !ledState;
      digitalWrite(LED_PIN, ledState);
      Serial.print("LED state toggled to: ");
      Serial.println(ledState == HIGH ? "ON" : "OFF");

      // 今回の処理時間を記録して、短期間での再実行を防ぐ
      lastDebounceTime = millis();
    }
  }

  // 今回のボタン状態を次回のループのために保存
  lastButtonState = reading;
}

void loop() {
  handleButton();
  // CPU リソースの過剰な消費を防ぐための短い待機
  delay(10);
}
