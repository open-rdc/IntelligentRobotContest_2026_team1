#include "servo.h"
#include "hardware/pwm.h"

static const uint SERVO_PIN = 18;
static const float PUSH_ANGLE = 73.0f;
static const float RETURN_ANGLE = -75.0f;

// PWMの周期設定: 50Hz (20ms = 20000us)
#define PWM_WRAP 20000

void servo_init(void) {
  gpio_set_function(SERVO_PIN, GPIO_FUNC_PWM);
  uint slice_num = pwm_gpio_to_slice_num(SERVO_PIN);

  // クロックを1MHzに設定 (1tick = 1us)
  // RP2040の標準sysclkは125MHzのため、分周比125.0で1MHzになる
  pwm_set_clkdiv(slice_num, 125.0f);
  pwm_set_wrap(slice_num, PWM_WRAP);

  // 初期位置を中央 (Futabaの標準である1520us) に設定
  pwm_set_chan_level(slice_num, pwm_gpio_to_channel(SERVO_PIN), 1520);

  pwm_set_enabled(slice_num, true);
}

void servo_set_pulse_width(uint16_t pulse_us) {
  uint slice_num = pwm_gpio_to_slice_num(SERVO_PIN);
  pwm_set_chan_level(slice_num, pwm_gpio_to_channel(SERVO_PIN), pulse_us);
}

void servo_set_angle(float angle_deg) {
  // Futaba S-U300: 中央1520us
  // 稼働範囲はおおよそ 60度あたり500usの変化
  float pulse = 1520.0f + angle_deg * (500.0f / 60.0f);

  // パルス幅を安全な範囲(500us〜2500us)に制限
  if (pulse < 500.0f)
    pulse = 500.0f;
  if (pulse > 2500.0f)
    pulse = 2500.0f;

  servo_set_pulse_width((uint16_t)pulse);
}

void servo_push(void) { servo_set_angle(PUSH_ANGLE); }

void servo_return(void) { servo_set_angle(RETURN_ANGLE); }
