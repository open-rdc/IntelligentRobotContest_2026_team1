#include "robot_api.h"
#include "logger.h"

// 全センサとモータ値のテスト出力
int main() {
  robot_init();

  while (1) {
    logger_update();
    robot_wait_ms(10); // 10ms周期でループを回すが、loggerは内部で100ms周期に制限する
  }
  return 0;
}