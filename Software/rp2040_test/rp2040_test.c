#include "robot_api.h"
#include <stdio.h>

// 全センサのテスト出力
int main() {
  robot_init();

  while (1) {
    uint16_t line[4];
    robot_get_line_sensors(line);

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

    robot_wait_ms(100);
  }
}