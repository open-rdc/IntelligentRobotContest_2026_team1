#include <stdio.h>

#include "bno055.h"
#include "camera.h"
#include "color_sensor.h"
#include "hardware/i2c.h"
#include "line_sensor.h"
#include "motor.h"
#include "pico/stdlib.h"
#include "sensor_data.h"
#include "servo.h"

SensorData g_sensor_data = {0};

// I2Cピンとパラメータ
static const uint I2C_SDA_PIN = 6;
static const uint I2C_SCL_PIN = 7;
static const uint I2C_FREQ = 400000;
static const uint SENSOR_INTERVAL_MS = 100;

#include "sensor_manager.h"

int main() {
  stdio_init_all();

  // サブモジュールの初期化
  camera_init();
  line_sensor_init();
  color_sensor_init();
  servo_init();
  motor_init();

  sleep_ms(2000);
  // I2C1 初期化 (BNO055用)
  i2c_init(i2c1, I2C_FREQ);
  gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
  gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
  gpio_pull_up(I2C_SDA_PIN);
  gpio_pull_up(I2C_SCL_PIN);

  sleep_ms(2000);
  printf("=== Contest Main ===\n");

  bool bno_ok = bno055_init(i2c1);
  if (!bno_ok) {
    printf("BNO055: 初期化失敗 (SDA=GP%d, SCL=GP%d, ADDR=0x%02X)\n",
           I2C_SDA_PIN, I2C_SCL_PIN, BNO055_ADDR);
  }

  uint32_t last_sensor_time = 0;
  uint32_t last_print_time = 0;

//   motor_set_speeds(-60, 60);
//   sleep_ms(2000);
//   motor_set_speeds(0, 0);

  while (true) {
    uint32_t now = to_ms_since_boot(get_absolute_time());

    // UART受信処理
    camera_poll();

    // センサデータの定期更新 (10ms周期)
    if (now - last_sensor_time >= 10) {
      last_sensor_time = now;

      update_sensors(bno_ok);
    }

    // まとめて出力 (保持しているデータを参照)
    if (now - last_print_time >= SENSOR_INTERVAL_MS) {
      last_print_time = now;
        print_sensors(bno_ok);
    }

    // ==========================================
    // メインロジック (ここにロボットの制御コードを追加)
    // ==========================================

    float error = (float)g_sensor_data.line_sensor[1] - (float)g_sensor_data.line_sensor[2];
    float error2 = (float)g_sensor_data.line_sensor[0] - (float)g_sensor_data.line_sensor[3];

    // float base_speed = 70.0f;
    // float kp = 0.5f;

    // float left_speed = base_speed + kp * error;
    // float right_speed = base_speed - kp * error;
    float left_speed = 70;
    float right_speed = 70;

    if (error2 > 20) {
        right_speed = -70;
    } else if (error < -20) {
        left_speed = -70;
    } else if (error > 20) {
        right_speed = 0;
    } else if (error < -20) {
        left_speed = 0;
    }

    // モータに速度指令を送信
    motor_set_speeds(left_speed, right_speed);
    // printf("line: %3d, %3d\n", g_sensor_data.line_sensor[1], g_sensor_data.line_sensor[2]);
    // printf("error: %3.f\n", error);
    // printf("motors: %3.f, %3.f\n", left_speed, right_speed);

    sleep_ms(50);
  }
}