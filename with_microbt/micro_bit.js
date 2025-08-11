/**
 * micro:bit MakeCode — BLE UART 安定版（ブロック変換対応）
 */
// 接続後に少し待って画面を通常状態へ戻す（ブロック変換に強いように関数で渡す）
function delayAndShowStateIcon () {
    basic.pause(300)
    showStateIcon()
}
// --- 接続/切断ハンドラ ---
bluetooth.onBluetoothConnected(function () {
    connected = true
    basic.showIcon(IconNames.Heart)
    control.inBackground(delayAndShowStateIcon)
})
bluetooth.onBluetoothDisconnected(function () {
    connected = false
    basic.showIcon(IconNames.No)
})
// --- A/B/A+B -> コマンド送信 ---
input.onButtonPressed(Button.A, function () {
    bluetooth.uartWriteString("ON\n")
})
// --- 改行区切りで受信処理（ブロック互換の delimiters 版） ---
bluetooth.onUartDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    s = bluetooth.uartReadUntil("\n")
    // 末尾の CR を除去（必要な場合）
    if (s.length > 0 && s.charAt(s.length - 1) == "\r") {
        s = s.substr(0, s.length - 1)
    }
    if (s.length == 0) {
        return
    }
    // 1) STATE:ON / STATE:OFF -> 画面更新（同じ状態は描画抑制）
    if (s.indexOf("STATE:") == 0) {
        v = s.substr(6)
        if (v == "ON" || v == "OFF") {
            if (lastState != v) {
                lastState = v
                showStateIcon()
            }
        }
        return
    }
    // 2) ESP?（キープアライブ）→ MBOK で応答（3 秒に 1 回まで）
    if (s == "ESP?") {
        now = control.millis()
        if (now - lastMbokMs >= MBOK_MIN_INTERVAL) {
            bluetooth.uartWriteString("MBOK\n")
            lastMbokMs = now
        }
        return
    }
})
input.onButtonPressed(Button.AB, function () {
    bluetooth.uartWriteString("TOGGLE\n")
})
input.onButtonPressed(Button.B, function () {
    bluetooth.uartWriteString("OFF\n")
})
// ms 最短間隔（ESP? への MBOK 応答）
// 状態アイコン表示
function showStateIcon () {
    if (lastState == "ON") {
        basic.showIcon(IconNames.Square)
    } else if (lastState == "OFF") {
        basic.showLeds(`
            . . . . .
            . . . . .
            . . . . .
            . . . . .
            . . # . .
            `)
    } else {
        // 未確定時は「?」風
        basic.showLeds(`
            . . # . .
            . # . # .
            . . . # .
            . . # . .
            . . # . .
            `)
    }
}
let lastMbokMs = 0
let now = 0
let v = ""
let s = ""
let connected = false
let lastState = ""
let MBOK_MIN_INTERVAL = 0
// ms 最短間隔（ESP? への MBOK 応答）
MBOK_MIN_INTERVAL = 3000
// --- 先に UART サービス起動（イベント取りこぼし防止）---
bluetooth.startUartService()
// --- 初期表示 ---
basic.showIcon(IconNames.No)
lastState = ""
