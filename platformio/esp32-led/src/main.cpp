#include <Arduino.h>

const int PIN_No = 19;

void setup() {
  Serial.begin(115200);       // シリアルモニタ初期化
  pinMode(PIN_No, OUTPUT);    // ピン19を出力に設定
  Serial.println("Setup complete");
}

void loop() {
  Serial.println("LED ON");
  digitalWrite(PIN_No, HIGH);
  delay(1000);

  Serial.println("LED OFF");
  digitalWrite(PIN_No, LOW);
  delay(1000);
}
