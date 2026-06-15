#include "sensor_manager.h"
#include "bno055.h"
#include "camera.h"
#include "color_sensor.h"
#include "line_sensor.h"
#include "sensor_data.h"
#include <stdio.h>

extern SensorData g_sensor_data;

// センサデータの更新
void update_sensors(bool bno_ok) {
  // BNO055 データ更新
  if (bno_ok) {
    if (!bno055_read_euler(&g_sensor_data.euler) ||
        !bno055_read_linear_accel(&g_sensor_data.accel)) {
      g_sensor_data.bno_error = true;
    } else {
      g_sensor_data.bno_error = false;
    }
  }

  // ライントレースセンサ・カラーセンサ データ更新
  line_sensor_read_all(g_sensor_data.line_sensor);
  color_sensor_read_all(g_sensor_data.color_sensor);
}

// センサデータの出力
void print_sensors(bool bno_ok) {
  //*
  // 1. UART Data
  if (g_sensor_data.camera_updated) {
    printf("Cam:[");
    for (int i = 0; i < g_sensor_data.camera_value_count; i++) {
      printf("%d", g_sensor_data.camera_values[i]);
      if (i < g_sensor_data.camera_value_count - 1)
        printf(" ");
    }
    printf("] ");
    g_sensor_data.camera_updated = false;
  } else {
    printf("Cam:[---] ");
  }

  // 2. BNO055 Data
  if (bno_ok) {
    if (g_sensor_data.bno_error) {
      printf("BNO:[Error] ");
    } else {
      printf("BNO:[%.1f] ", g_sensor_data.euler.x);
    }
  } else {
    printf("BNO:[NotInit] ");
  }

  // 3. Line Sensor Data
  printf("Line:[");
  for (int i = 0; i < 4; i++) {
    printf("S%d=%4d", i, g_sensor_data.line_sensor[i]);
    if (i < 3) {
      printf(" ");
    }
  }
  printf("] ");

  // 4. Color Sensor Data
  printf("Color:[B=%4d G=%4d R=%4d]\n", g_sensor_data.color_sensor[0],
         g_sensor_data.color_sensor[1], g_sensor_data.color_sensor[2]);
  //*/
  // for (int i = 0; i < 4; i++) {
  //   printf(">Sensor%d:%d\n", i, g_sensor_data.line_sensor[i]);
  // }
}
