#ifndef MOTOR_H
#define MOTOR_H

#include "pico/stdlib.h"

// モータのPWM出力の初期化 (GP4,5:右モータ / GP8,9:左モータ)
void motor_init(void);

// 個別モータの回転速度を設定 (speed: -100.0 ~ 100.0)
void motor_right_set_speed(float speed);
void motor_left_set_speed(float speed);

// 左右モータの回転速度を同時に設定 (speed: -100.0 ~ 100.0)
void motor_set_speeds(float left, float right);

#endif // MOTOR_H
