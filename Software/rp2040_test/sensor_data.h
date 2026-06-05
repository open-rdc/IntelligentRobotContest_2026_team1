#ifndef SENSOR_DATA_H
#define SENSOR_DATA_H

#include "pico/stdlib.h"
#include "bno055.h"
#include <stdbool.h>

// 取得したデータを保持する構造体
typedef struct {
  int camera_values[16];
  int camera_value_count;
  bool camera_updated;

  bno055_vec3_t euler;
  bno055_vec3_t accel;
  bool bno_error;

  uint16_t line_sensor[4];
} SensorData;

extern SensorData g_sensor_data;

#endif // SENSOR_DATA_H
