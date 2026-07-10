#include "robot_api.h"
#include "logger.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>

// --- 制御定数 (p_control.pyの値を0-100スケールに変換) ---
#define BASE_SPEED       60.0f   // 0.6 * 100
#define KP_INNER         0.15f    // センサが0-100なので係数はそのまま
#define KP_OUTER         0.10f
#define CROSS_TH         20      // 0.2 * 100
#define LINE_LOST_TH     95      // 0.95 * 100
#define LINE_FOUND_TH    70      // 0.7 * 100
#define TURN_TOLERANCE   3.0f    // [deg]
#define TURN_SPEED       60.0f   // 0.6 * 100
#define DEAD_ZONE_COMP   50.0f   // 0.5 * 100


// ===== ユーティリティ =====

// 角度を -180 ~ 180 の範囲に正規化する
static float normalize_angle(float a) {
  a = fmodf(a + 180.0f, 360.0f);
  if (a < 0) a += 360.0f;
  return a - 180.0f;
}

// 外側2つのセンサが両方ともしきい値以下なら交差点と判定する
static bool is_cross(uint16_t line[4]) {
  return line[0] < CROSS_TH && line[3] < CROSS_TH;
}


// ===== 基本動作関数 =====

// P制御による1ステップ分のライントレースを実行する
// センサを読み取り、P制御でモータ出力を設定する
static void trace_step(uint16_t line[4]) {
    float base_speed = 10.0f;
  robot_get_line_sensors(line);
  float inner_error = (float)line[1] - (float)line[2];
  float outer_error = (float)line[0] - (float)line[3];
  float correction = KP_INNER * inner_error + KP_OUTER * outer_error;
  float left = base_speed + correction;
  float right = base_speed - correction;

  // 不感帯補償
  if (left > 0) left += DEAD_ZONE_COMP;
  else if (left < 0) left -= DEAD_ZONE_COMP;
  if (right > 0) right += DEAD_ZONE_COMP;
  else if (right < 0) right -= DEAD_ZONE_COMP;

  robot_set_motor(left, right);
}

// 指定した絶対角度まで旋回する
static void turn_abs(float target) {
  while (1) {
    float error = normalize_angle(robot_get_imu_yaw() - target);
    if (fabsf(error) <= TURN_TOLERANCE) break;
    if (error > 0)
      robot_set_motor(TURN_SPEED, -TURN_SPEED);
    else
      robot_set_motor(-TURN_SPEED, TURN_SPEED);
    robot_wait_ms(100); // ログが早すぎないように100msに変更
  }
  robot_set_motor(0, 0);
}

// 現在角度から指定した角度だけ旋回する
static void turn_rel(float delta) {
  float target = normalize_angle(robot_get_imu_yaw() + delta);
  turn_abs(target);
}

// 一定時間モータを駆動して停止する
static void drive_timed(uint32_t ms, float left, float right) {
  robot_set_motor(left, right);
  robot_wait_ms(ms);
  robot_set_motor(0, 0);
}

// P制御でライントレースしながら指定時間走行する
static void trace_for(uint32_t ms) {
  uint32_t elapsed = 0;
  uint16_t line[4];
  while (elapsed < ms) {
    trace_step(line);
    robot_wait_ms(10);
    elapsed += 10;
  }
  robot_set_motor(0, 0);
}

// 交差点まで走行する
// trace: true=P制御でライントレース, false=固定出力で直進
static void move_to_cross(float speed, bool trace) {
  uint16_t line[4];
  while (1) {
    if (trace) {
      trace_step(line);
    } else {
      robot_get_line_sensors(line);
      robot_set_motor(speed, speed);
    }
    if (is_cross(line)) break;
    robot_wait_ms(10);
  }
  robot_set_motor(0, 0);
}

// ラインを見失った際に左右に首振りしてラインを探す
static void search_line(float range_deg) {
  float pre_yaw = robot_get_imu_yaw();
  uint16_t line[4];

  // 左旋回で探索
  robot_set_motor(-TURN_SPEED, TURN_SPEED);
  while (normalize_angle(robot_get_imu_yaw() - pre_yaw) < range_deg) {
    robot_get_line_sensors(line);
    if (line[1] < LINE_FOUND_TH && line[2] < LINE_FOUND_TH) {
      printf("Line Found\n");
      return;
    }
    robot_wait_ms(10);
  }

  // 右旋回で探索
  robot_set_motor(TURN_SPEED, -TURN_SPEED);
  while (normalize_angle(robot_get_imu_yaw() - pre_yaw) > -range_deg) {
    robot_get_line_sensors(line);
    if (line[1] < LINE_FOUND_TH && line[2] < LINE_FOUND_TH) {
      printf("Line Found\n");
      return;
    }
    robot_wait_ms(10);
  }

  // 見つからなかった場合は元の角度に戻って前進する
  turn_abs(pre_yaw);
  printf("Line Not Found\n");
  drive_timed(1000, BASE_SPEED, BASE_SPEED);
}

// 指定した色のボールがカメラの中央（X=160付近）に来るように旋回する
// target_color: 1=Red, 2=Yellow, 3=Blue
// 戻り値: true=中央合わせ成功, false=ボールを見失った
static bool align_to_ball(int target_color) {
  int cam[32];
  float kp = 0.3f;         // P制御の比例ゲイン
  int tolerance = 15;      // 許容誤差 (ピクセル)
  int lost_count = 0;      // ボールを見失った連続フレーム数

  while (1) {
    int cam_count = robot_get_camera(cam, 32);
    
    if (cam_count > 0) {
      // 新しいフレームを受信
      if (cam_count == 1 && cam[0] == 0) {
        // 何もボールが検出されなかった
        lost_count++;
      } else if (cam_count % 5 == 0) {
        int best_x = -1;
        int max_mag = -1;
        
        // 対象色の中で最も確信度(magnitude)が高いものを探す
        for (int i = 0; i < cam_count; i += 5) {
          if (cam[i] == target_color) {
            if (cam[i+4] > max_mag) {
              max_mag = cam[i+4];
              best_x = cam[i+1];
            }
          }
        }
        
        if (best_x >= 0) {
          lost_count = 0; // 見つけたのでリセット
          int error = best_x - 160;
          
          if (abs(error) <= tolerance) {
            // 許容誤差内に入ったら停止して成功を返す
            robot_set_motor(0, 0);
            return true;
          }
          
          // ボールが右(X>160)にある場合、右旋回（左モータ正、右モータ負）
          float speed = error * kp;
          
          // 最低速度と最高速度の制限（モータの不感帯を乗り越えるため）
          float min_speed = 30.0f;
          float max_speed = 60.0f;
          
          if (speed > 0) {
            speed += min_speed;
            if (speed > max_speed) speed = max_speed;
          } else {
            speed -= min_speed;
            if (speed < -max_speed) speed = -max_speed;
          }
          
          robot_set_motor(speed, -speed);
        } else {
          // 対象色のボールがなかった
          lost_count++;
        }
      }
      
      // 連続で10フレーム(約300ms)見失ったら諦める
      if (lost_count > 10) {
        robot_set_motor(0, 0);
        return false;
      }
    }
    
    // 新しいフレームがない場合はそのままのモータ出力で待機
    robot_wait_ms(10);
  }
}

// ===== コース固有の動作 =====

static void drop_to_blue(void) {
  move_to_cross(BASE_SPEED, false);
  turn_abs(180);
  robot_wait_ms(1000);
  turn_abs(90);
  move_to_cross(BASE_SPEED, false);
  turn_abs(-90);
}

static void drop_to_yellow(void) {
  // TODO
}

static void drop_to_red(void) {
  // TODO
}


// ===== メイン制御 =====

void main_control(void) {
  int cross_count = 0;
  uint16_t line[4];

  // 変数定義


  while (1) {
    trace_step(line);

    logger_update();
    robot_wait_ms(10);
    continue;

    if (is_cross(line)) {
      cross_count++;
      printf("cross: %d\n", cross_count);
      robot_set_motor(0, 0);
      robot_wait_ms(500);
      drive_timed(200, BASE_SPEED, BASE_SPEED);

      if (cross_count == 2) {
        turn_abs(180);
        robot_wait_ms(2000);
        turn_abs(0);
        drive_timed(200, BASE_SPEED, BASE_SPEED);
      }
      if (cross_count == 6) {
        drive_timed(500, -BASE_SPEED, -BASE_SPEED);
        turn_abs(0);
      }
      if (cross_count == 8) {
        drop_to_blue();
      } else if (cross_count == 11) {
        drive_timed(3000, BASE_SPEED, BASE_SPEED);
        break;
      }
    }

    if (line[1] > LINE_LOST_TH && line[2] > LINE_LOST_TH && cross_count > 1 && cross_count < 10) {
      printf("Line Lost\n");
      search_line(45.0f);
    }

    robot_wait_ms(10);
  }
}

int main() {
  robot_init();
  main_control();
  return 0;
}