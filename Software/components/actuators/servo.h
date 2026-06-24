#ifndef SERVO_H
#define SERVO_H

#include "pico/stdlib.h"
#include <stdint.h>

// サーボの初期化 (GP18)
void servo_init(void);

// サーボのパルス幅を指定して角度を制御 (Futaba標準: 1520usが中央)
void servo_set_pulse_width(uint16_t pulse_us);

// 角度を指定して制御 (-60度〜+60度程度を想定)
void servo_set_angle(float angle_deg);

// ボールの押し出し・引き戻し
void servo_push(void);
void servo_return(void);

#endif // SERVO_H
