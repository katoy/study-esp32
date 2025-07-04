const int PIN_No = 19;

void setup() {
  Serial.begin(115200);  // デバッグ用のシリアル通信開始
  pinMode(PIN_No, OUTPUT);
  Serial.println("Setup complete");  // 初期化完了メッセージ
}

void loop() {
  Serial.println("LED ON");
  digitalWrite(PIN_No, HIGH);
  delay(250);

  Serial.println("LED OFF");
  digitalWrite(PIN_No, LOW);
  delay(250);
}
