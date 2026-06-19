#ifndef BNO055_H
#define BNO055_H

#include "hardware/i2c.h"

// I2Cアドレス (ADR=LOW: 0x28, ADR=HIGH: 0x29)
static const uint8_t BNO055_ADDR = 0x28;

// 3次元ベクトル
typedef struct {
    float x, y, z;
} bno055_vec3_t;

// 初期化 (NDOFモード, 成功:true)
bool bno055_init(i2c_inst_t *i2c_port);

// オイラー角 [deg]: x=yaw, y=roll, z=pitch
bool bno055_read_euler(bno055_vec3_t *euler);

// 線形加速度 [m/s^2]
bool bno055_read_linear_accel(bno055_vec3_t *accel);

#endif
