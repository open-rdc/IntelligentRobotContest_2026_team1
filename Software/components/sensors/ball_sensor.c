#include "ball_sensor.h"
#include "hardware/gpio.h"

#define BALL_SENSOR_PIN 19

void ball_sensor_init(void) {
  gpio_init(BALL_SENSOR_PIN);
  gpio_set_dir(BALL_SENSOR_PIN, GPIO_IN);
  // プルアップは基板側で実装されているため、Pico内部のプルアップは設定しない
}

bool ball_sensor_read(void) {
  // ボールあり(LOW)=0 の場合にtrueを返す
  return !gpio_get(BALL_SENSOR_PIN);
}
