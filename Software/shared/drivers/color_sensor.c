#include "color_sensor.h"
#include "hardware/adc.h"

// 27=B, 28=G, 29=R
static const uint COLOR_B_PIN = 27; // ADC1
static const uint COLOR_G_PIN = 28; // ADC2
static const uint COLOR_R_PIN = 29; // ADC3

void color_sensor_init(void) {
  // ADC自体の初期化は line_sensor_init で行われている想定
  // ここでは各ピンのADC機能を有効化
  adc_gpio_init(COLOR_B_PIN);
  adc_gpio_init(COLOR_G_PIN);
  adc_gpio_init(COLOR_R_PIN);
}

void color_sensor_read_all(uint16_t out_values[3]) {
  adc_select_input(1); // 27番ピン (ADC1)
  out_values[0] = adc_read();

  adc_select_input(2); // 28番ピン (ADC2)
  out_values[1] = adc_read();

  adc_select_input(3); // 29番ピン (ADC3)
  out_values[2] = adc_read();
}
