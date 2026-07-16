#include "logger.h"
#include "robot_api.h"
#include <stdio.h>

static uint32_t last_print = 0;

void logger_update(void) {
  uint32_t now = robot_get_time_ms();
  if (now - last_print >= 100) {
    last_print = now;

    // カメラ
    int cam[32];
    int cam_count = robot_get_camera(cam, 32);
    if (cam_count > 0) {
      if (cam_count == 1 && cam[0] == 0) {
        printf("Cam:[No Balls] ");
      } else if (cam_count % 5 == 0) {
        printf("Cam:[");
        for (int i = 0; i < cam_count; i += 5) {
          const char *color_str = "Unknown";
          if (cam[i] == 1)
            color_str = "Red";
          else if (cam[i] == 2)
            color_str = "Yellow";
          else if (cam[i] == 3)
            color_str = "Blue";

          printf("{C:%-6s X:%3d Y:%3d R:%3d}", color_str, cam[i + 1],
                 cam[i + 2], cam[i + 3]);
          if (i + 4 < cam_count)
            printf(" ");
        }
        printf("] ");
      } else {
        printf("Cam:[Format Error] ");
      }
    } else {
      printf("Cam:[Timeout] ");
    }

    // IMU
    float yaw = robot_get_imu_yaw();
    printf("Yaw:[%.1f] ", yaw);

    // ラインセンサ
    uint16_t line[4];
    robot_get_line_sensors(line);
    printf("Line:[S0=%4d S1=%4d S2=%4d S3=%4d] ", line[0], line[1], line[2],
           line[3]);

    // カラーセンサ
    uint16_t color[3];
    robot_get_color_sensor(color);
    printf("Color:[B=%4d G=%4d R=%4d] ", color[0], color[1], color[2]);

    // ボールセンサ
    bool has_ball = robot_get_ball_sensor();
    printf("Ball:[%s] ", has_ball ? "True" : "False");

    // モータ出力
    float motor_l, motor_r;
    robot_get_motor_speeds(&motor_l, &motor_r);
    printf("Motor:[L=%4.0f R=%4.0f]", motor_l, motor_r);

    printf("\n");
  }
}
