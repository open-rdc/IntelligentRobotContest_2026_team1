#include "robot_api.h"
#include "bno055.h"
#include "camera.h"
#include "color_sensor.h"
#include "line_sensor.h"
#include "motor.h"
#include "sensor_data.h"
#include "servo.h"
#include "ball_sensor.h"
#include "hardware/i2c.h"
#include <stdio.h>
#include "pico/stdio_usb.h"
// I2Cピンとパラメータ
static const uint I2C_SDA_PIN = 6;
static const uint I2C_SCL_PIN = 7;
static const uint I2C_FREQ = 400000;

// 内部状態
SensorData g_sensor_data = {0};
static bool bno_ok = false;
static float imu_offset = 0.0f;

void robot_init(void) {
  stdio_init_all();

  // USB CDCの接続確立を待機 (最大5秒)
  for (int i = 0; i < 50 && !stdio_usb_connected(); i++) {
    sleep_ms(100);
  }

  // サブモジュールの初期化
  camera_init();
  line_sensor_init();
  color_sensor_init();
  servo_init();
  motor_init();
  ball_sensor_init();

  sleep_ms(2000);

  // I2C1 初期化 (BNO055用)
  i2c_init(i2c1, I2C_FREQ);
  gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
  gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
  gpio_pull_up(I2C_SDA_PIN);
  gpio_pull_up(I2C_SCL_PIN);

  sleep_ms(2000);

  bno_ok = bno055_init(i2c1);
  if (!bno_ok) {
    printf("BNO055: 初期化失敗 (SDA=GP%d, SCL=GP%d, ADDR=0x%02X)\n",
           I2C_SDA_PIN, I2C_SCL_PIN, BNO055_ADDR);
  }

  imu_offset = 0.0f;
  printf("=== Robot API Initialized ===\n");
}

void robot_set_motor(float left, float right) {
  motor_set_speeds(left, right);
}

void robot_get_motor_speeds(float* left, float* right) {
  motor_get_speeds(left, right);
}

void robot_wait_ms(uint32_t ms) {
  // 待機中もカメラのUART受信を処理する
  uint32_t start = to_ms_since_boot(get_absolute_time());
  while (to_ms_since_boot(get_absolute_time()) - start < ms) {
    camera_poll();
    sleep_ms(1);
  }
}

void robot_get_line_sensors(uint16_t out[4]) {
  line_sensor_read_all(out);
}

float robot_get_imu_yaw(void) {
  if (!bno_ok) return 0.0f;
  bno055_vec3_t euler;
  if (!bno055_read_euler(&euler)) return 0.0f;
  return euler.x - imu_offset;
}

void robot_reset_imu(void) {
  if (!bno_ok) return;
  bno055_vec3_t euler;
  if (bno055_read_euler(&euler)) {
    imu_offset = euler.x;
  }
}

void robot_get_color_sensor(uint16_t out[3]) {
  color_sensor_read_all(out);
}

int robot_get_camera(int out[], int max_count) {
  // 更新がなければ0を返す
  if (!g_sensor_data.camera_updated) return 0;

  int count = g_sensor_data.camera_value_count;
  if (count > max_count) count = max_count;
  for (int i = 0; i < count; i++) {
    out[i] = g_sensor_data.camera_values[i];
  }
  g_sensor_data.camera_updated = false;
  return count;
}

bool robot_get_ball_sensor(void) {
  return ball_sensor_read();
}

uint32_t robot_get_time_ms(void) {
  return to_ms_since_boot(get_absolute_time());
}

void robot_servo_push(void) {
  servo_push();
}

void robot_servo_return(void) {
  servo_return();
}
