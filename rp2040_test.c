#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/timer.h"

// UART0の設定(UnitVからのメッセージ受信用)
#define UART0_ID uart0
#define BAUD_RATE 115200
#define UART0_TX_PIN 0
#define UART0_RX_PIN 1

int main() {
    // 標準入出力の初期化(USBシリアルでのREPL相当)
    stdio_init_all();

    // UART0の初期化とピン設定
    uart_init(UART0_ID, BAUD_RATE);
    gpio_set_function(UART0_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART0_RX_PIN, GPIO_FUNC_UART);

    // USBシリアルの接続が安定するまで少し待機(任意)
    sleep_ms(2000);
    printf("UART Test Started (Receiving on UART0)...\n");

    // 最後にデータを受信した時刻を記録(ミリ秒)
    uint32_t last_receive_time = to_ms_since_boot(get_absolute_time());

    while (true) {
        uint32_t current_time = to_ms_since_boot(get_absolute_time());

        // UART0にデータが来ているか確認
        if (uart_is_readable(UART0_ID)) {
            last_receive_time = current_time; // 受信時刻を更新
            
            printf("UART0 -> PC : ");
            
            // データがある限り読み込み続ける
            while (uart_is_readable(UART0_ID)) {
                uint8_t ch = uart_getc(UART0_ID);
                
                // USBシリアル(PC)へ出力
                putchar((char)ch);
            }
            printf("\n");
        } else {
            // 一定時間(3000ミリ秒)データが来ていない場合の処理
            if ((current_time - last_receive_time) > 3000) {
                printf("UART0: No data received...\n");
                // メッセージが連続で出すぎないように時刻をリセット
                last_receive_time = current_time;
            }
        }

        sleep_ms(10);
    }

    return 0;
}