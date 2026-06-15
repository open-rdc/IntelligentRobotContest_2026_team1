#include "motor.h"
#include "hardware/pwm.h"

#define MOTOR_RIGHT_A 4
#define MOTOR_RIGHT_B 5
#define MOTOR_LEFT_A 8
#define MOTOR_LEFT_B 9

// PWM周波数: 40kHz
#define PWM_FREQ 40000
// RP2040のシステムクロックはデフォルト125MHz
#define SYS_CLK 125000000
#define PWM_WRAP (SYS_CLK / PWM_FREQ) // 125MHz / 40kHz = 3125

void motor_init(void) {
  // ピンをPWM機能に設定
  gpio_set_function(MOTOR_RIGHT_A, GPIO_FUNC_PWM);
  gpio_set_function(MOTOR_RIGHT_B, GPIO_FUNC_PWM);
  gpio_set_function(MOTOR_LEFT_A, GPIO_FUNC_PWM);
  gpio_set_function(MOTOR_LEFT_B, GPIO_FUNC_PWM);

  // 8,9番ピンのPWMスライスを取得 (共にスライス4)
  uint slice1 = pwm_gpio_to_slice_num(MOTOR_RIGHT_A);
  // 10,11番ピンのPWMスライスを取得 (共にスライス5)
  uint slice2 = pwm_gpio_to_slice_num(MOTOR_LEFT_A);

  // モータ1用PWM設定
  pwm_set_clkdiv(slice1, 1.0f);
  pwm_set_wrap(slice1, PWM_WRAP - 1);
  pwm_set_chan_level(slice1, PWM_CHAN_A, 0);
  pwm_set_chan_level(slice1, PWM_CHAN_B, 0);
  pwm_set_enabled(slice1, true);

  // モータ2用PWM設定
  pwm_set_clkdiv(slice2, 1.0f);
  pwm_set_wrap(slice2, PWM_WRAP - 1);
  pwm_set_chan_level(slice2, PWM_CHAN_A, 0);
  pwm_set_chan_level(slice2, PWM_CHAN_B, 0);
  pwm_set_enabled(slice2, true);
}

// 内部関数：指定したピンペアに対して-100~100の範囲でPWMを出力
static void set_motor_pwm(uint pin_a, uint pin_b, float speed) {
  uint slice = pwm_gpio_to_slice_num(pin_a);
  uint chan_a = pwm_gpio_to_channel(pin_a);
  uint chan_b = pwm_gpio_to_channel(pin_b);

  if (speed > 100.0f) speed = 100.0f;
  if (speed < -100.0f) speed = -100.0f;

  float abs_speed = speed >= 0 ? speed : -speed;
  uint16_t duty = (uint16_t)(PWM_WRAP * (abs_speed / 100.0f));

  if (speed > 0) {
    // 正転
    pwm_set_chan_level(slice, chan_a, duty);
    pwm_set_chan_level(slice, chan_b, 0);
  } else if (speed < 0) {
    // 逆転
    pwm_set_chan_level(slice, chan_a, 0);
    pwm_set_chan_level(slice, chan_b, duty);
  } else {
    // 停止
    pwm_set_chan_level(slice, chan_a, 0);
    pwm_set_chan_level(slice, chan_b, 0);
  }
}

void motor_right_set_speed(float speed) {
  set_motor_pwm(MOTOR_RIGHT_A, MOTOR_RIGHT_B, -speed);
}

void motor_left_set_speed(float speed) {
  set_motor_pwm(MOTOR_LEFT_A, MOTOR_LEFT_B, speed);
}

void motor_set_speeds(float left_speed, float right_speed) {
  motor_left_set_speed(left_speed);
  motor_right_set_speed(right_speed);
}
