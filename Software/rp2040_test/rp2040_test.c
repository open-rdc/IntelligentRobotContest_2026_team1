#include "bno055.h"
#include "line_sensor.h"
#include "sensor_data.h"
#include "camera.h"
#include "hardware/i2c.h"
#include "pico/stdlib.h"
#include <stdio.h>

SensorData g_sensor_data = {0};

// I2Cピンとパラメータ
static const uint I2C_SDA_PIN = 6;
static const uint I2C_SCL_PIN = 7;
static const uint I2C_FREQ = 400000;
static const uint SENSOR_INTERVAL_MS = 100;

int main() {
  stdio_init_all();

  // サブモジュールの初期化
  camera_init();
  line_sensor_init();

  // I2C1 初期化 (BNO055用)
  i2c_init(i2c1, I2C_FREQ);
  gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
  gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
  gpio_pull_up(I2C_SDA_PIN);
  gpio_pull_up(I2C_SCL_PIN);

  sleep_ms(2000);
  printf("=== RP2040 テスト (Camera + BNO055 + Line) ===\n");

  bool bno_ok = bno055_init(i2c1);
  if (!bno_ok) {
    printf("BNO055: 初期化失敗 (SDA=GP%d, SCL=GP%d, ADDR=0x%02X)\n",
           I2C_SDA_PIN, I2C_SCL_PIN, BNO055_ADDR);
  }

  uint32_t last_sensor_time = 0;
  uint32_t last_print_time = 0;

  while (true) {
    uint32_t now = to_ms_since_boot(get_absolute_time());

    // UART受信処理
    camera_poll();

    // センサデータの定期更新 (10ms周期)
    if (now - last_sensor_time >= 10) {
      last_sensor_time = now;

      // BNO055 データ更新
      if (bno_ok) {
        if (!bno055_read_euler(&g_sensor_data.euler) ||
            !bno055_read_linear_accel(&g_sensor_data.accel)) {
          g_sensor_data.bno_error = true;
        } else {
          g_sensor_data.bno_error = false;
        }
      }

      // ライントレースセンサ データ更新
      line_sensor_read_all(g_sensor_data.line_sensor);
    }

    // まとめて出力 (保持しているデータを参照)
    if (now - last_print_time >= SENSOR_INTERVAL_MS) {
      last_print_time = now;
/*
      // 1. UART Data
      if (g_sensor_data.camera_updated) {
        printf("Cam:[");
        for (int i = 0; i < g_sensor_data.camera_value_count; i++) {
          printf("%d", g_sensor_data.camera_values[i]);
          if (i < g_sensor_data.camera_value_count - 1) printf(" ");
        }
        printf("] ");
        g_sensor_data.camera_updated = false;
      } else {
        printf("Cam:[---] ");
      }

      // 2. BNO055 Data
      if (bno_ok) {
        if (g_sensor_data.bno_error) {
          printf("BNO:[Error] ");
        } else {
          // printf("BNO:[Y=%.1f R=%.1f P=%.1f aX=%.2f aY=%.2f aZ=%.2f] ",
          //        g_sensor_data.euler.x, g_sensor_data.euler.y,
          //        g_sensor_data.euler.z, g_sensor_data.accel.x,
          //        g_sensor_data.accel.y, g_sensor_data.accel.z);
          printf("BNO:[%.1f] ", g_sensor_data.euler.x);
        }
      } else {
        printf("BNO:[NotInit] ");
      }

      // 3. Line Sensor Data
      printf("Line:[");
      for (int i = 0; i < 4; i++) {
        printf("S%d=%4d", i, g_sensor_data.line_sensor[i]);
        if (i < 3) {
          printf(" ");
        }
      }
      printf("]\n");
*/
      for (int i = 0; i < 4; i++) {
        printf(">Sensor%d:%d\n", i, g_sensor_data.line_sensor[i]);
      }
    }

    sleep_ms(2);
  }
}