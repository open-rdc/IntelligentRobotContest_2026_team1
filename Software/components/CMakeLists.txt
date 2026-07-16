# 共有コンポーネントライブラリ (components)
# contest / rp2040_test の両プロジェクトから参照される

# ソースファイル一覧
set(SHARED_SOURCES
    ${CMAKE_CURRENT_LIST_DIR}/api/robot_api.c
    ${CMAKE_CURRENT_LIST_DIR}/sensors/bno055.c
    ${CMAKE_CURRENT_LIST_DIR}/sensors/camera.c
    ${CMAKE_CURRENT_LIST_DIR}/sensors/color_sensor.c
    ${CMAKE_CURRENT_LIST_DIR}/sensors/line_sensor.c
    ${CMAKE_CURRENT_LIST_DIR}/sensors/ball_sensor.c
    ${CMAKE_CURRENT_LIST_DIR}/actuators/motor.c
    ${CMAKE_CURRENT_LIST_DIR}/actuators/servo.c
    ${CMAKE_CURRENT_LIST_DIR}/utils/logger.c
)

# インクルードパス一覧
set(SHARED_INCLUDES
    ${CMAKE_CURRENT_LIST_DIR}/api
    ${CMAKE_CURRENT_LIST_DIR}/sensors
    ${CMAKE_CURRENT_LIST_DIR}/actuators
    ${CMAKE_CURRENT_LIST_DIR}/common
    ${CMAKE_CURRENT_LIST_DIR}/utils
)
