let device, characteristic;

const SERVICE_UUID = '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
const CHARACTERISTIC_UUID = 'beb5483e-36e1-4688-b7f5-ea07361b26a8';

// Bluetooth接続を行う関数
document.getElementById('connect').addEventListener('click', async () => {
  try {
    console.log('Requesting Bluetooth Device...');
    device = await navigator.bluetooth.requestDevice({
      filters: [{ services: [SERVICE_UUID] }]
    });

    console.log('Device Selected:', device.name);
    console.log('Connecting to GATT Server...');
    const server = await device.gatt.connect();

    console.log('Getting Service...');
    const service = await server.getPrimaryService(SERVICE_UUID);

    console.log('Getting Characteristic...');
    characteristic = await service.getCharacteristic(CHARACTERISTIC_UUID);

    console.log('Connected successfully!');
  } catch (error) {
    console.log('Argh! ' + error);
  }
});

// コマンドをESP32に送信する関数
function sendCommand(command) {
  if (device && characteristic) {
    console.log('Sending command: ' + command);
    characteristic.writeValue(new TextEncoder().encode(command))
      .then(_ => {
        console.log('Command sent successfully');
      })
      .catch(error => {
        console.error('Error sending command: ', error);
      });
  } else {
    console.log('Device not connected.');
  }
}

// 各ボタンにイベントリスナーを設定
['on', 'off'].forEach(direction => {
  document.getElementById(direction).addEventListener('click', () => {
    sendCommand(direction);
  });
});
