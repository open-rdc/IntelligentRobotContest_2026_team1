#ifndef BALL_SENSOR_H
#define BALL_SENSOR_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void ball_sensor_init(void);

// ボール保持状態を返す (true=保持あり(LOW), false=なし(HIGH))
bool ball_sensor_read(void);

#ifdef __cplusplus
}
#endif

#endif // BALL_SENSOR_H
