// ESP32 BLE Arduino（Kolban/標準コアのBLE）を使う場合 =====
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// BLEサービスとキャラクタリスティックのUUID
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"


const int ledPin = 19;
bool ledState = LOW;
BLECharacteristic *pCharacteristic;


class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String value = pCharacteristic->getValue();
      if (value.length() > 0) {
        if (value[0] == '1') {
          ledState = HIGH;
          digitalWrite(ledPin, ledState);
          Serial.println("LED ON (BLE)");
        } else if (value[0] == '0') {
          ledState = LOW;
          digitalWrite(ledPin, ledState);
          Serial.println("LED OFF (BLE)");
        }
      }
    }
};

void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, ledState);

  BLEDevice::init("ESP32_LED");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_WRITE_NR |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pCharacteristic->addDescriptor(new BLE2902());
  pCharacteristic->setValue("0");
  pCharacteristic->setCallbacks(new MyCallbacks());
  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
  Serial.println("BLEサーバー起動完了。スマホから接続してキャラクタリスティックを書き換えてください。");
}


void loop() {
  // BLEはイベント駆動なので、loop内で特に処理不要
  delay(100);
}
