# 共有ドライバライブラリ (shared)
# contest / rp2040_test の両プロジェクトから参照される

# ソースファイル一覧
set(SHARED_SOURCES
    ${CMAKE_CURRENT_LIST_DIR}/drivers/bno055.c
    ${CMAKE_CURRENT_LIST_DIR}/drivers/camera.c
    ${CMAKE_CURRENT_LIST_DIR}/drivers/color_sensor.c
    ${CMAKE_CURRENT_LIST_DIR}/drivers/line_sensor.c
    ${CMAKE_CURRENT_LIST_DIR}/drivers/motor.c
    ${CMAKE_CURRENT_LIST_DIR}/drivers/servo.c
    ${CMAKE_CURRENT_LIST_DIR}/robot_api.c
)

# インクルードパス一覧
set(SHARED_INCLUDES
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/drivers
)
