#include "robot_api.h"
#include <stdio.h>

// p_control.pyに準拠したメイン制御関数
void main_control(void) {
  uint32_t last_print = 0;

  robot_set_motor(100, 100);

  while (1) {
    uint16_t line[4];
    robot_get_line_sensors(line);

    // デバッグ出力 (100ms周期)
    uint32_t now = robot_get_time_ms();
    if (now - last_print >= 100) {
      last_print = now;

      // カメラ
      int cam[16];
      int cam_count = robot_get_camera(cam, 16);
      if (cam_count > 0) {
        printf("Cam:[");
        for (int i = 0; i < cam_count; i++) {
          printf("%d", cam[i]);
          if (i < cam_count - 1) printf(" ");
        }
        printf("] ");
      } else {
        printf("Cam:[---] ");
      }

      // IMU
      float yaw = robot_get_imu_yaw();
      printf("BNO:[%.1f] ", yaw);

      // ラインセンサ
      printf("Line:[S0=%4d S1=%4d S2=%4d S3=%4d] ",
             line[0], line[1], line[2], line[3]);

      // カラーセンサ
      uint16_t color[3];
      robot_get_color_sensor(color);
      printf("Color:[B=%4d G=%4d R=%4d]\n", color[0], color[1], color[2]);
    }

    // P制御
    float error = (float)line[1] - (float)line[2];
    float error2 = (float)line[0] - (float)line[3];

    float base_speed = 10.0f;
    float kp = 0.2f;
    float kp2 = 0.5f;

    float left = base_speed + (kp * error + kp2 * error2);
    float right = base_speed - (kp * error + kp2 * error2);

    // 不感帯補償
    if (left > 0) {
      left += 50;
    } else if (left < 0) {
      left -= 50;
    }
    if (right > 0) {
      right += 50;
    } else if (right < 0) {
      right -= 50;
    }

    // robot_set_motor(left, right);
    robot_wait_ms(50);
  }
}

int main() {
  robot_init();
  main_control();
  return 0;
}