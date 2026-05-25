# P制御によるライントレースのサンプル
import sys
import os
import math

# パッケージのインポートパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator import Simulator


def p_controller(line_sensors, state) :
    # 重み付き平均でライン偏差を計算するP制御
    n = len(line_sensors)
    weights = [i - (n - 1) / 2.0 for i in range(n)]

    weighted_sum = 0.0
    total_darkness = 0.0
    for i, val in enumerate(line_sensors) :
        darkness = 1.0 - val  # 黒=1, 白=0に反転
        weighted_sum += weights[i] * darkness
        total_darkness += darkness

    error = weighted_sum / total_darkness if total_darkness > 0.01 else 0.0

    base_speed = 0.5
    kp = 0.5
    left = base_speed - kp * error
    right = base_speed + kp * error
    return (left, right)


def main() :
    course_path = os.path.join(
        os.path.dirname(__file__), '..', 'courses', 'contest_course.jpeg')

    sim = Simulator(course_path, controller_fn=p_controller)

    # ロボットの初期位置（コース画像に合わせて調整）
    # sim.set_robot_pose(650, 300, -math.pi / 2)
    sim.set_robot_pose(615, 1930, -math.pi / 2)

    sim.run()


if __name__ == '__main__' :
    main()
