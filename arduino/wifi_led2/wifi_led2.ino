#include <WiFi.h>

#include "config.h"
#include "index.h"
#include "style.h"

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

  // WiFi接続
  Serial.println("WiFiに接続中...");
  WiFi.begin(ssid, password);

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
        // Serial.write(c); // デバッグ用に無効化

        // 行が終わった場合
        if (c == '\n') {
          // HTTPリクエストの終了を確認
          if (currentLine.length() == 0) {
            
            // HTTPレスポンスを送信
            client.println("HTTP/1.1 200 OK");

            if (header.indexOf("GET /style.css") >= 0) {
              Serial.println("CSSを送信");
              client.println("Content-type:text/css");
              client.println("Connection: close");
              client.println();
              client.print(STYLE_CSS);
            } else {
              if (header.indexOf("GET /LED_ON") >= 0) {
                Serial.println("LED ON");
                ledState = HIGH;
                digitalWrite(ledPin, ledState);
              } else if (header.indexOf("GET /LED_OFF") >= 0) {
                Serial.println("LED OFF");
                ledState = LOW;
                digitalWrite(ledPin, ledState);
              }
              
              Serial.println("HTMLを送信");
              client.println("Content-type:text/html");
              client.println("Connection: close");
              client.println();

              // HTMLを生成
              String html = INDEX_HTML;
              if(ledState) {
                html.replace("%STATE%", "ON");
                html.replace("%STATE_CLASS%", "on");
              } else {
                html.replace("%STATE%", "OFF");
                html.replace("%STATE_CLASS%", "off");
              }
              client.print(html);
            }

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
