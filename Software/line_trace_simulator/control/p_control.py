import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator import Simulator

# --- 制御定数 ---
BASE_SPEED = 0.6
KP_INNER = 0.2
KP_OUTER = 0.5
CROSS_TH = 0.2   # 交差点検出しきい値
LINE_LOST_TH = 0.95  # ライン見失い判定しきい値
LINE_FOUND_TH = 0.7
TURN_TOLERANCE = 3.0  # 旋回完了判定角度 [deg]
TURN_SPEED = 0.6
DEAD_ZONE = 0.5


# ===== ユーティリティ =====

def normalize_angle(a) :
    # 角度を -180 ~ 180 の範囲に正規化する
    return (a + 180) % 360 - 180

def is_cross(line, th=CROSS_TH) :
    # 外側2つのセンサが両方ともしきい値以下なら交差点と判定する
    return line[0] < th and line[3] < th


# ===== 基本動作関数 =====

def trace_step(robot, base_speed=0.1) :
    # P制御による1ステップ分のライントレースを実行する
    # センサを読み取り、P制御でモータ出力を設定し、センサ値を返す
    line = robot.get_line_sensors()
    inner_error = line[1] - line[2]
    outer_error = line[0] - line[3]
    speed = KP_INNER * inner_error + KP_OUTER * outer_error
    left_speed = base_speed - speed
    right_speed = base_speed + speed
    
    if left_speed > 0 :
        left_speed += DEAD_ZONE
    elif left_speed < 0 :
        left_speed -= DEAD_ZONE
    if right_speed > 0 :
        right_speed += DEAD_ZONE
    elif right_speed < 0 :
        right_speed -= DEAD_ZONE
        
    robot.start_motor(left_speed, right_speed)
    return line


def turn_abs(robot, target) :
    # 指定した絶対角度まで旋回する
    while True :
        error = normalize_angle(robot.get_imu_yaw() - target)
        if abs(error) <= TURN_TOLERANCE :
            break
        if error > 0 :
            robot.start_motor(TURN_SPEED, -TURN_SPEED)
        else :
            robot.start_motor(-TURN_SPEED, TURN_SPEED)
        robot.wait(0.01)
    robot.start_motor(0, 0)

def turn_rel(robot, delta) :
    # 現在角度から指定した角度だけ旋回する
    target = normalize_angle(robot.get_imu_yaw() + delta)
    turn_abs(robot, target)

def drive_timed(robot, seconds, left, right=None) :
    # 一定時間モータを駆動して停止する
    if right is None :
        right = left
    robot.start_motor(left, right)
    robot.wait(seconds)
    robot.start_motor(0, 0)

def trace_for(robot, seconds, speed=BASE_SPEED) :
    # P制御でライントレースしながら指定時間走行する
    elapsed = 0.0
    dt = 0.01
    while elapsed < seconds :
        trace_step(robot, speed)
        robot.wait(dt)
        elapsed += dt
    robot.start_motor(0, 0)

def move_to_cross(robot, speed=BASE_SPEED, trace=True) :
    # 交差点まで走行する
    # trace=True: P制御でライントレースしながら走行する
    # trace=False: 固定出力で直進する (ライン上にいない場合向け)
    while True :
        if trace :
            line = trace_step(robot)
        else :
            line = robot.get_line_sensors()
            robot.start_motor(speed, speed)
        if is_cross(line) :
            break
        robot.wait(0.01)
    robot.start_motor(0, 0)

def search_line(robot, range_deg=45) :
    # ラインを見失った際に左右に首振りしてラインを探す
    pre_yaw = robot.get_imu_yaw()

    # 左旋回で探索
    robot.start_motor(-TURN_SPEED, TURN_SPEED)
    while normalize_angle(robot.get_imu_yaw() - pre_yaw) < range_deg :
        line = robot.get_line_sensors()
        if line[1] < LINE_FOUND_TH and line[2] < LINE_FOUND_TH :
            print('Line Found')
            return
        robot.wait(0.01)

    # 右旋回で探索 (左側の限界から右側の限界まで)
    robot.start_motor(TURN_SPEED, -TURN_SPEED)
    while normalize_angle(robot.get_imu_yaw() - pre_yaw) > -range_deg :
        line = robot.get_line_sensors()
        if line[1] < LINE_FOUND_TH and line[2] < LINE_FOUND_TH :
            print('Line Found')
            return
        robot.wait(0.01)

    # 見つからなかった場合は元の角度に戻って前進する
    turn_abs(robot, pre_yaw)
    print('Line Not Found')
    drive_timed(robot, 1.0, BASE_SPEED)


# ===== コース固有の動作 =====

def drop_to_blue(robot) :
    move_to_cross(robot, trace=False)
    turn_abs(robot, 180)
    robot.wait(1.0)
    turn_abs(robot, 90)
    move_to_cross(robot, trace=False)
    turn_abs(robot, -90)

def drop_to_yellow(robot) :
    pass

def drop_to_red(robot) :
    pass


# ===== メイン制御 =====

def main_control(robot) :
    cross_count = 0

    while True :
        line = trace_step(robot)

        if is_cross(line) :
            cross_count += 1
            print('cross:', cross_count)
            robot.start_motor(0, 0)
            robot.wait(0.5)
            drive_timed(robot, 0.2, BASE_SPEED)

            if cross_count == 2 :
                turn_abs(robot, 180)
                robot.wait(2.0)
                turn_abs(robot, 0)
                drive_timed(robot, 0.2, BASE_SPEED)
            if cross_count == 6 :
                drive_timed(robot, 0.5, -BASE_SPEED)
                turn_abs(robot, 0)
            if cross_count == 8 :
                drop_to_blue(robot)
            elif cross_count == 11 :
                drive_timed(robot, 3.0, BASE_SPEED)
                break

        if line[1] > LINE_LOST_TH and line[2] > LINE_LOST_TH and 1 < cross_count < 10 :
            print('Line Lost')
            search_line(robot)

        robot.wait(0.01)


def main() :
    course_path = os.path.join(os.path.dirname(__file__), '..', 'courses', 'contest_course.jpeg')

    sim = Simulator(course_path, controller_fn=main_control)
    sim.set_robot_pose(615, 1930, -90.0)
    sim.set_line_sensor_params(
        fov_radius=5.0,
        sensor_height=1.0,
        half_angle=60.0,
        noise_std=0.1
    )
    sim.set_imu_params(noise_std=5.0)
    sim.run()

if __name__ == '__main__' :
    main()
