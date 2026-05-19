#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/i2c.h"
#include "bno055.h"

// ピン設定
static const uint UART0_TX_PIN = 0;
static const uint UART0_RX_PIN = 1;
static const uint I2C_SDA_PIN  = 6;
static const uint I2C_SCL_PIN  = 7;

// パラメータ
static const uint UART_BAUD          = 115200;
static const uint I2C_FREQ           = 400000;
static const uint BNO055_INTERVAL_MS = 100;
static const uint UART_TIMEOUT_MS    = 3000;

int main() {
    stdio_init_all();

    // UART0 初期化 (UnitVからの受信用)
    uart_init(uart0, UART_BAUD);
    gpio_set_function(UART0_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART0_RX_PIN, GPIO_FUNC_UART);

    // I2C1 初期化 (BNO055用)
    i2c_init(i2c1, I2C_FREQ);
    gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA_PIN);
    gpio_pull_up(I2C_SCL_PIN);

    sleep_ms(2000);
    printf("=== RP2040 テスト (UART + BNO055) ===\n");

    bool bno_ok = bno055_init(i2c1);
    if (!bno_ok) {
        printf("BNO055: 初期化失敗 (SDA=GP%d, SCL=GP%d, ADDR=0x%02X)\n",
               I2C_SDA_PIN, I2C_SCL_PIN, BNO055_ADDR);
    }

    uint32_t last_rx_time  = to_ms_since_boot(get_absolute_time());
    uint32_t last_bno_time = 0;

    while (true) {
        uint32_t now = to_ms_since_boot(get_absolute_time());

        // UART0 受信 → PC転送
        if (uart_is_readable(uart0)) {
            last_rx_time = now;
            printf("UART0 -> PC : ");
            while (uart_is_readable(uart0)) {
                putchar(uart_getc(uart0));
            }
            printf("\n");
        } else if (now - last_rx_time > UART_TIMEOUT_MS) {
            printf("UART0: No data received...\n");
            last_rx_time = now;
        }

        // BNO055 定期読み取り
        if (bno_ok && now - last_bno_time >= BNO055_INTERVAL_MS) {
            last_bno_time = now;
            bno055_vec3_t euler, accel;

            if (bno055_read_euler(&euler)) {
                printf("BNO055 Euler: Y=%.1f R=%.1f P=%.1f", euler.x, euler.y, euler.z);
            } else {
                printf("BNO055 Euler: 読み取り失敗");
            }

            if (bno055_read_linear_accel(&accel)) {
                printf("  Accel: X=%.2f Y=%.2f Z=%.2f", accel.x, accel.y, accel.z);
            }
            printf("\n");
        }

        sleep_ms(10);
    }
}