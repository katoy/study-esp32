const char INDEX_HTML[] = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<title>ESP32 LED Control</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="/style.css">
</head>
<body>
<div class="container">
  <h1>ESP32 LED Control</h1>
  <p class="status %STATE_CLASS%">LED is currently <strong>%STATE%</strong></p>
  <div class="buttons">
    <a href="/LED_ON" class="btn btn-on">Turn ON</a>
    <a href="/LED_OFF" class="btn btn-off">Turn OFF</a>
  </div>
</div>
</body>
</html>
)rawliteral";