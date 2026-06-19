#ifndef COLOR_SENSOR_H
#define COLOR_SENSOR_H

#include "pico/stdlib.h"
#include <stdint.h>

// カラーセンサの初期化
void color_sensor_init(void);

// カラーセンサの読み取り (Blue, Green, Redの順)
void color_sensor_read_all(uint16_t out_values[3]);

#endif // COLOR_SENSOR_H
