#include <Arduino.h>
#include <WiFi.h>
#include "secrets.h"

// secrets.h から設定を取得

// サーバーの設定
WiFiServer server(80);
String header; // HTTPリクエストのヘッダー

// LEDピンの設定
const int ledPin = 19;
bool ledState = LOW;

void setup() {
  // シリアルモニタの初期化
  Serial.begin(115200);

  // LEDピンを出力モードに設定
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, ledState);

  // 固定IPアドレスの設定
  if (!WiFi.config(LOCAL_IP, GATEWAY, SUBNET, DNS1, DNS2)) {
    Serial.println("[ERROR] IPアドレスの設定に失敗しました");
  }

  // WiFi接続
  Serial.println("WiFiに接続中...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFiに接続完了!");
  Serial.println("IPアドレス: ");
  Serial.println(WiFi.localIP());

  // サーバーを開始
  server.begin();
}

void loop() {
  WiFiClient client = server.available(); // クライアント接続の確認

  if (client) { // クライアントが接続した場合
    Serial.println("クライアントが接続しました");
    String currentLine = ""; // 現在の受信行を保存

    while (client.connected()) {
      if (client.available()) { // データが利用可能か確認
        char c = client.read();
        header += c;
        Serial.write(c);

        // 行が終わった場合
        if (c == '\n') {
          // HTTPリクエストの終了を確認
          if (currentLine.length() == 0) {
            // リクエストに応じてLEDを制御
            if (header.indexOf("GET /LED_ON") >= 0) {
              Serial.println("LED ON");
              ledState = HIGH;
              digitalWrite(ledPin, ledState);
            } else if (header.indexOf("GET /LED_OFF") >= 0) {
              Serial.println("LED OFF");
              ledState = LOW;
              digitalWrite(ledPin, ledState);
            }

            // HTTPレスポンスを送信
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println("Connection: close");
            client.println();

            // HTMLを生成
            client.println("<!DOCTYPE html><html>");
            client.println("<head><title>ESP32 LED Control</title></head>");
            client.println("<body>");
            client.println("<h1>ESP32 LED Control</h1>");
            client.println("<p>LED is currently " + String(ledState ? "ON" : "OFF") + "</p>");
            client.println("<p><a href=\"/LED_ON\">Turn ON</a></p>");
            client.println("<p><a href=\"/LED_OFF\">Turn OFF</a></p>");
            client.println("</body></html>");

            // HTTPリクエストの処理終了
            break;
          } else {
            currentLine = ""; // 次の行に進む
          }
        } else if (c != '\r') {
          currentLine += c; // 受信した行を追加
        }
      }
    }

    // クライアントを切断
    client.stop();
    Serial.println("クライアントを切断しました");

    // ヘッダーのリセット
    header = "";
  }
}