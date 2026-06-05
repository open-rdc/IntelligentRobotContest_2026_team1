import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator import Simulator

def main_control(robot) :
    cross_count = 0

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
            robot.start_motor(0, 0)
            robot.wait(0.5)
            move_motor(robot, 0.1, 0.5)

            if cross_count == 2 :
                turn_abs(robot, 180)
                robot.wait(2.0)
                turn_abs(robot, 0)
            if cross_count == 6 :
                move_motor(robot, 0.5, -0.5)
                turn_abs(robot, 0)
            if cross_count == 8 :
                drop_to_blue(robot)
            elif cross_count == 11 :
                move_motor(robot, 2.0, 0.5)
                break

        robot.start_motor(left, right)
        robot.wait(0.01)

def drop_to_blue(robot) :
    move_to_cross(robot)
    turn_abs(robot, 180)
    robot.wait(1.0)
    turn_abs(robot, 90)
    move_to_cross(robot)
    turn_abs(robot, -90)

def drop_to_yellow(robot) :
    pass

def drop_to_red(robot) :
    pass

def turn_abs(robot, target_angle) :
    while abs(error := robot.get_imu_yaw() - target_angle) > 3 :
        error = (error + 180) % 360 - 180
        if error > 0 :
            robot.start_motor(0.3, -0.3)
        else :
            robot.start_motor(-0.3, 0.3)
        robot.wait(0.01)
    robot.start_motor(0,0)

def move_motor(robot, time, l, r=None) :
    if r is None :
        r = l
    robot.start_motor(l, r)
    robot.wait(time)
    robot.start_motor(0, 0)

def move_to_cross(robot, power=0.5) :
    line = robot.get_line_sensors()
    while not (line[0] < 0.2 and line[3] < 0.2) :
        robot.start_motor(power, power)
        robot.wait(0.01)
        line = robot.get_line_sensors()
    robot.start_motor(0, 0)

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
