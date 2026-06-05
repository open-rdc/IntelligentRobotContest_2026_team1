#ifndef LINE_SENSOR_H
#define LINE_SENSOR_H

#include "pico/stdlib.h"
#include <stdint.h>

// ライントレースセンサの初期化
void line_sensor_init(void);

// ライントレースセンサの4チャンネルすべての値を読み取る
void line_sensor_read_all(uint16_t out_values[4]);

#endif // LINE_SENSOR_H
