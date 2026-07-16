#ifndef ROBOT_API_H
#define ROBOT_API_H

#include "pico/stdlib.h"
#include <stdint.h>
#include <stdbool.h>

// ロボットAPIの初期化 (全ハードウェアの初期化を内部で実行)
void robot_init(void);

// モータ出力の設定 (-100.0 ~ 100.0)
void robot_set_motor(float left, float right);

// 現在のモータ出力値を取得
void robot_get_motor_speeds(float* left, float* right);

// 指定ミリ秒の待機 (内部でカメラのUART受信を処理)
void robot_wait_ms(uint32_t ms);

// ラインセンサの値を取得 (0~100の正規化済み値)
void robot_get_line_sensors(uint16_t out[4]);

// IMUのヨー角を取得 [deg]
float robot_get_imu_yaw(void);

// IMUのヨー角をリセット (現在の角度を0とする)
void robot_reset_imu(void);

// カラーセンサの値を取得 (B, G, Rの順)
void robot_get_color_sensor(uint16_t out[3]);

// ボール保持状態を取得 (true=保持あり, false=なし)
bool robot_get_ball_sensor(void);

// カメラの最新値を取得
// 戻り値: 値の個数 (0 = 前回取得時から更新なし)
int robot_get_camera(int out[], int max_count);

// 経過時間を取得 [ms]
uint32_t robot_get_time_ms(void);

// サーボ操作
void robot_servo_push(void);
void robot_servo_return(void);

#endif // ROBOT_API_H
