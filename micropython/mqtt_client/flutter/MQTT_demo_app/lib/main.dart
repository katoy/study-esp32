import 'package:flutter/material.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';
import 'dart:convert';
import 'dart:async';

// メッセージ履歴表示部品（トップレベル）
class MessageHistoryArea extends StatelessWidget {
  final List<String> messages;
  const MessageHistoryArea({required this.messages, Key? key})
    : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Scrollbar(
        child: ListView.builder(
          itemCount: messages.length,
          itemBuilder: (context, idx) => Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            child: Text(
              messages[idx],
              style: TextStyle(fontSize: 14, color: Colors.blueGrey[700]),
            ),
          ),
        ),
      ),
    );
  }
}

Future<MqttServerClient> setupMqttClient() async {
  const brokerAddress = '192.168.0.104';
  const clientId = 'flutter_client';
  const topicName = 'esp32/led/status';
  final client = MqttServerClient(brokerAddress, clientId);
  client.logging(on: false);
  client.keepAlivePeriod = 60;
  // 状態メッセージを外部からセットできるようにする
  MqttLedPanel.connectionStatus = 'Connecting...';
  client.onConnected = () => MqttLedPanel.connectionStatus = 'Client connected';
  client.onDisconnected = () =>
      MqttLedPanel.connectionStatus = 'Client disconnected';
  client.onSubscribed = (topic) =>
      MqttLedPanel.connectionStatus = 'Subscribed to topic: ' + topic;
  client.connectionMessage = MqttConnectMessage()
      .withClientIdentifier(clientId)
      .withWillTopic('willtopic')
      .withWillMessage('My Will message')
      .startClean()
      .withWillQos(MqttQos.atLeastOnce);
  await client.connect('YOUR_USERNAME', 'YOUR_PASSWORD');
  client.subscribe(topicName, MqttQos.atLeastOnce);
  return client;
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final client = await setupMqttClient();
  runApp(MyApp(client));
}

class MyApp extends StatelessWidget {
  final MqttClient client;
  const MyApp(this.client, {Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.grey[100],
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.black,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            padding: EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            textStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
        ),
      ),
      home: Scaffold(
        appBar: AppBar(title: Text('ESP32 LED Controller'), centerTitle: true),
        body: Center(child: MqttLedPanel(client: client)),
      ),
    );
  }
}

class MqttLedPanel extends StatefulWidget {
  final MqttClient client;
  static String connectionStatus = '';
  const MqttLedPanel({required this.client, Key? key}) : super(key: key);
  @override
  State<MqttLedPanel> createState() => _MqttLedPanelState();
}

class _MqttLedPanelState extends State<MqttLedPanel> {
  late final Timer _statusTimer;
  String? latestMessage;
  final List<String> statusMessages = [];

  @override
  void initState() {
    super.initState();
    widget.client.updates?.listen(_onMqttMessage);
    _statusTimer = Timer.periodic(Duration(milliseconds: 500), (timer) {
      if (mounted) {
        setState(() {
          if (MqttLedPanel.connectionStatus.isNotEmpty) {
            if (statusMessages.isEmpty ||
                statusMessages.last != MqttLedPanel.connectionStatus) {
              statusMessages.add(MqttLedPanel.connectionStatus);
            }
          }
        });
      }
    });
  }

  void _onMqttMessage(List<MqttReceivedMessage<MqttMessage>> c) {
    final now = DateTime.now();
    final timeStr =
        '[${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')} ]';
    final recMess = c[0];
    final topic = recMess.topic;
    final mqttMsg = recMess.payload as MqttPublishMessage;
    final payload = mqttMsg.payload.message;
    final String receivedMessage = utf8.decode(payload);
    setState(() {
      latestMessage = receivedMessage;
    });
    MqttLedPanel.connectionStatus =
        '$timeStr Received: [' + topic + '] ' + receivedMessage;
  }

  @override
  void dispose() {
    _statusTimer.cancel();
    super.dispose();
  }

  void publishMessage(String msg) {
    final builder = MqttClientPayloadBuilder();
    builder.addString(msg);
    const pubTopic = 'esp32/led/cmd';
    widget.client.publishMessage(
      pubTopic,
      MqttQos.atLeastOnce,
      builder.payload!,
      retain: false,
    );
    _addStatusMessage('Published', pubTopic, msg);
  }

  void _addStatusMessage(String type, String topic, String msg) {
    final now = DateTime.now();
    final timeStr =
        '[${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')} ]';
    final statusMsg = '$timeStr $type: [$topic] $msg';
    MqttLedPanel.connectionStatus = statusMsg;
    setState(() {
      statusMessages.add(statusMsg);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(maxWidth: 400),
      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 16,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            'ESP32 LED の状態',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.black,
            ),
          ),
          SizedBox(height: 12),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey[200],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              latestMessage ?? '未受信',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
            ),
          ),
          SizedBox(height: 32),
          Text(
            'ESP32 LED スイッチ',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.black,
            ),
          ),
          SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton(
                onPressed: () => publishMessage('on'),
                child: Text('on'),
              ),
              SizedBox(width: 24),
              ElevatedButton(
                onPressed: () => publishMessage('off'),
                child: Text('off'),
              ),
            ],
          ),
          SizedBox(height: 32),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('状態メッセージ履歴', style: TextStyle(fontWeight: FontWeight.bold)),
              TextButton(
                onPressed: () {
                  setState(() {
                    statusMessages.clear();
                  });
                },
                child: Text('クリア'),
              ),
            ],
          ),
          SizedBox(height: 8),
          Expanded(child: MessageHistoryArea(messages: statusMessages)),
        ],
      ),
    );
  }
}
