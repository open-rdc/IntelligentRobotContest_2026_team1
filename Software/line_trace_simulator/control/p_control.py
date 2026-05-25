import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator import Simulator

def main_control(robot) :
    cross_count = 0
    
    # robot.move_motor(0.5, 0.5)
    # robot.wait(0.01)

    while True :
        line = robot.get_line_sensors()
        error = line[1] - line[2]
        base_speed = 0.5
        kp = 0.5
        left = base_speed - kp * error
        right = base_speed + kp * error

        if line[0] < 0.2 and line[3] < 0.2 :
            cross_count += 1
            print('corss: ', cross_count)
            robot.move_motor(0, 0)
            robot.wait(0.5)
            robot.move_motor(0.5, 0.5)
            robot.wait(0.1)

            if cross_count == 6 :
                while abs(robot.get_imu_yaw()) > 0.05 :
                    robot.move_motor(0.3, -0.3)
                    robot.wait(0.01)
            elif cross_count == 11 :
                robot.move_motor(0.5, 0.5)
                robot.wait(2.0)
                robot.move_motor(0, 0)
                break

        robot.move_motor(left, right)
        robot.wait(0.01)

def main() :
    course_path = os.path.join(os.path.dirname(__file__), '..', 'courses', 'contest_course.jpeg')

    sim = Simulator(course_path, controller_fn=main_control)
    sim.set_robot_pose(615, 1930, -math.pi / 2)
    sim.set_line_sensor_params(noise_std=0.1)
    sim.set_imu_params(noise_std=0.1)
    sim.run()

if __name__ == '__main__' :
    main()
