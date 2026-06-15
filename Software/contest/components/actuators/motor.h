#ifndef MOTOR_H
#define MOTOR_H

#include "pico/stdlib.h"

// モータのPWM出力の初期化 (8,9番ピン:モータ1 / 10,11番ピン:モータ2)
void motor_init(void);

// モータの回転速度を設定 (speed: -100.0 ~ 100.0)
void motor_right_set_speed(float speed);
void motor_left_set_speed(float speed);
void motor_set_speeds(float left_speed, float right_speed);

#endif // MOTOR_H
