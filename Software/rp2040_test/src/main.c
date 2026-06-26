#include "logger.h"
#include "robot_api.h"

// 全センサとモータ値のテスト出力
int main() {
  robot_init();
  static uint32_t last_print = 0;

  while (1) {
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
          if (i < cam_count - 1)
            printf(" ");
        }
        printf("] ");
      } else {
        printf("Cam:[---] ");
      }

      // IMU
      float yaw = robot_get_imu_yaw();
      printf("BNO:[%.1f] ", yaw);

      // ラインセンサ
      uint16_t line[4];
      robot_get_line_sensors(line);
      printf("Line:[S0=%4d S1=%4d S2=%4d S3=%4d] ", line[0], line[1], line[2],
             line[3]);

      // カラーセンサ
      uint16_t color[3];
      robot_get_color_sensor(color);
      printf("Color:[B=%4d G=%4d R=%4d] ", color[0], color[1], color[2]);

      // モータ出力
      float motor_l, motor_r;
      robot_get_motor_speeds(&motor_l, &motor_r);
      printf("Motor:[L=%4.0f R=%4.0f]\n", motor_l, motor_r);
    }

    robot_wait_ms(
        10); // 10ms周期でループを回すが、loggerは内部で100ms周期に制限する
  }
  return 0;
}