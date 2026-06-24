#include "line_sensor.h"
#include "hardware/adc.h"

static const uint MUX_S0_PIN = 17;
static const uint MUX_S1_PIN = 16;
static const uint ADC_PIN = 26;

// キャリブレーション値 (contest版)
static const uint MIN_VAL[4] = {1000, 650, 700, 700};
// static const uint MAX_VAL[4] = {3800, 3800, 3800, 3800};
static const uint MAX_VAL[4] = {2800, 2800, 2500, 2800};

void line_sensor_init(void) {
  // ADCとマルチプレクサ初期化
  adc_init();
  adc_gpio_init(ADC_PIN);
  adc_select_input(0); // 26番ピンはADC0

  gpio_init(MUX_S0_PIN);
  gpio_set_dir(MUX_S0_PIN, GPIO_OUT);
  gpio_init(MUX_S1_PIN);
  gpio_set_dir(MUX_S1_PIN, GPIO_OUT);
}

void line_sensor_read_all(uint16_t out_values[4]) {
  // カラーセンサ等で別のADCチャンネルが選択されている可能性があるため、ここでADC0に切り替える
  adc_select_input(0);

  for (int i = 0; i < 4; i++) {
    gpio_put(MUX_S0_PIN, i & 0x01);
    gpio_put(MUX_S1_PIN, (i >> 1) & 0x01);
    sleep_us(10);

    uint16_t raw_val = adc_read();
    if (raw_val < MIN_VAL[i]) {
      out_values[i] = 0;
    } else if (raw_val > MAX_VAL[i]) {
      out_values[i] = 100;
    } else {
      out_values[i] = (raw_val - MIN_VAL[i]) * 100 / (MAX_VAL[i] - MIN_VAL[i]);
    }

    // out_values[i] = raw_val; // 生値確認用
  }
}
