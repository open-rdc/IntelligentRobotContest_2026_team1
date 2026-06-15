#ifndef CAMERA_H
#define CAMERA_H

#include "pico/stdlib.h"
#include <stdbool.h>

// UART(Camera)の初期化
void camera_init(void);

// UARTの受信バッファを確認し、1行分受信していればg_sensor_dataを更新する
void camera_poll(void);

#endif // CAMERA_H
