import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator import Simulator


def main_task(robot) :
    # マイコン風の逐次的な制御プログラム

    # 開始前に1秒待機する
    robot.wait(1.0)
    
    # 0.5秒間まっすぐ前進する
    robot.move_motor(0.5, 0.5)
    robot.wait(0.5)
    
    # モータを停止して0.5秒待機する
    robot.move_motor(0.0, 0.0)
    robot.wait(0.5)
    
    # IMUを使って90度(約1.57rad)旋回する
    start_yaw = robot.get_imu_yaw()
    robot.move_motor(0.3, -0.3)
    
    while True :
        current_yaw = robot.get_imu_yaw()
        # 角度の差分を計算（-π〜πに収まるように補正）
        diff = current_yaw - start_yaw
        diff = math.atan2(math.sin(diff), math.cos(diff))
        
        if abs(diff) >= math.pi / 2 :
            break
            
        robot.wait(0.01) # 短い時間待機してループを回す
        
    # 旋回停止
    robot.move_motor(0.0, 0.0)
    robot.wait(0.5)
    
    # P制御でライントレースを開始する
    while True :
        line_sensors = robot.get_line_sensors()
        if len(line_sensors) >= 4 :
            error = line_sensors[1] - line_sensors[2]
            base_speed = 0.5
            kp = 0.5
            robot.move_motor(base_speed - kp * error, base_speed + kp * error)
        
        # 1msループをシミュレート
        robot.wait(0.001)


def main() :
    course_path = os.path.join(os.path.dirname(__file__), '..', 'courses', 'contest_course.jpeg')

    # マイコンモードを使用するため、1引数の関数(main_task)を渡す
    sim = Simulator(course_path, controller_fn=main_task)
    sim.set_robot_pose(615, 1930, -math.pi / 2)
    
    # IMUのノイズを設定
    sim.set_imu_params(noise_std=0.01)
    
    sim.run()


if __name__ == '__main__' :
    main()
