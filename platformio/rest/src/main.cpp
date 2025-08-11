

#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include "secrets.h"

#define LED_PIN 19 // LEDを接続するGPIOピン番号

AsyncWebServer server(80);

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);

    // 固定IPアドレスの設定
  IPAddress local_IP(LOCAL_IP_ADDR);      // 固定したいIPアドレス
  IPAddress gateway(GATEWAY_ADDR);        // ゲートウェイ
  IPAddress subnet(SUBNET_MASK);          // サブネットマスク
  WiFi.config(local_IP, gateway, subnet); // 固定IPアドレスを設定
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);   // WiFi接続開始

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  server.on("/led/on", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(LED_PIN, HIGH);
    request->send(200, "text/plain", "LED ON");
  });

  server.on("/led/off", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(LED_PIN, LOW);
    request->send(200, "text/plain", "LED OFF");
  });

  server.on("/led/reset", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(LED_PIN, LOW);
    delay(100);
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    request->send(200, "text/plain", "LED RESET");
  });

  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Origin", "*");
  server.begin();
}

void loop() {
  // ...existing code...
}