/**
 * BLE UART を使って A/B/A+B で ON/OFF/TOGGLE を送信
 */
// micro:bit MakeCode (JavaScript)
bluetooth.onBluetoothConnected(function () {
    connected = true
    basic.showIcon(IconNames.Heart)
})
bluetooth.onBluetoothDisconnected(function () {
    connected = false
    basic.showIcon(IconNames.No)
})
// A/B/A+B でコマンド送信（末尾に \n）
input.onButtonPressed(Button.A, function () {
    bluetooth.uartWriteString("ON\n")
})
input.onButtonPressed(Button.AB, function () {
    bluetooth.uartWriteString("TOGGLE\n")
})
input.onButtonPressed(Button.B, function () {
    bluetooth.uartWriteString("OFF\n")
})
// 中央からの "ESP?" に応答
bluetooth.onUartDataReceived("\n", function () {

})
let connected = false
// UARTサービスを開始
bluetooth.startUartService()
basic.showIcon(IconNames.No)
