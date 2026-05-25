import pygame
import sys
import os
import inspect
import threading
from simulator.course import CourseModel
from simulator.robot import RobotModel
from simulator.line_sensor import LineSensorModel
from simulator.imu import IMUModel
from simulator.renderer import Renderer
from simulator.robot_api import RobotAPI


class Simulator :
    # ライントレースシミュレータのメインクラス

    # 速度倍率の選択肢
    SPEED_OPTIONS = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]

    def __init__(self, course_path, controller_fn=None) :
        # course_path: コース画像のパス
        # controller_fn: ユーザ制御関数
        self._course_path = course_path
        self._controller_fn = controller_fn

        # モデル
        self.course = CourseModel()
        self.robot = RobotModel()
        self.line_sensor = LineSensorModel()
        self.imu = IMUModel()
        self.api = RobotAPI()

        # シミュレーション設定
        self.dt = 0.001          # 物理演算の時間刻み [s]
        self.fps = 60            # 描画FPS
        self.speed_index = 3     # SPEED_OPTIONSのインデックス (1.0x)

        # 状態
        self._running = False
        self._sim_time = 0.0
        self._line_sensor_values = []
        self._user_thread = None
        self._renderer = None

    def set_robot_params(self, **kwargs) :
        for key, val in kwargs.items() :
            if hasattr(self.robot, key) :
                setattr(self.robot, key, val)

    def set_line_sensor_params(self, **kwargs) :
        for key, val in kwargs.items() :
            if hasattr(self.line_sensor, key) :
                setattr(self.line_sensor, key, val)

    def set_imu_params(self, **kwargs) :
        for key, val in kwargs.items() :
            if hasattr(self.imu, key) :
                setattr(self.imu, key, val)

    def set_controller(self, fn) :
        self._controller_fn = fn

    def set_robot_pose(self, x, y, theta) :
        self.robot.set_pose(x, y, theta)

    @property
    def speed_multiplier(self) :
        return self.SPEED_OPTIONS[self.speed_index]

    def _reset(self) :
        # 古いスレッドを停止させる
        if self.api :
            with self.api._lock :
                self.api._resetting = True
                self.api._time_cond.notify_all()
        
        # APIインスタンスを新しく作り直す
        self.api = RobotAPI()

        # シミュレーションをリセットする
        self.robot.reset()
        self.imu.reset(self.robot.theta)
        self._sim_time = 0.0
        self._line_sensor_values = []
        self._running = False
        
        if self._renderer :
            self._renderer.clear_trail()
            
        # 初回のセンサ値読み取り
        self._read_sensors()
        print('[Simulator] Reset')
        
        # ユーザースレッドを再スタート
        self._start_user_thread()

    def _start_user_thread(self) :
        # ユーザー制御関数をスレッドで起動
        if not self._controller_fn :
            return False
            
        def run_user_program() :
            try :
                self._controller_fn(self.api)
            except SystemExit :
                pass  # リセットや終了による安全な停止
            except Exception as e :
                print(f"[Simulator] User program error: {e}")
        
        self._user_thread = threading.Thread(target=run_user_program, daemon=True)
        self._user_thread.start()
        return True

    def _handle_events(self) :
        # イベント処理 (Falseを返すと終了)
        for event in pygame.event.get() :
            if event.type == pygame.QUIT :
                return False
            if event.type == pygame.KEYDOWN :
                if event.key == pygame.K_ESCAPE :
                    return False
                elif event.key == pygame.K_SPACE :
                    self._running = not self._running
                    print(f'[Simulator] {"Started" if self._running else "Paused"}')
                elif event.key == pygame.K_r :
                    self._reset()
                elif event.key == pygame.K_UP :
                    self.speed_index = min(self.speed_index + 1, len(self.SPEED_OPTIONS) - 1)
                    print(f'[Simulator] Speed: {self.speed_multiplier}x')
                elif event.key == pygame.K_DOWN :
                    self.speed_index = max(self.speed_index - 1, 0)
                    print(f'[Simulator] Speed: {self.speed_multiplier}x')
                elif event.key == pygame.K_t :
                    if self._renderer :
                        self._renderer.show_trail = not self._renderer.show_trail
        return True

    def _read_sensors(self) :
        self._line_sensor_values = self.line_sensor.read(self.robot.state, self.course)

    def _step_simulation(self) :
        # 1ステップ分の物理演算とセンサ読み取り
        self._read_sensors()

        # APIからの指令を読み取る
        with self.api._lock :
            u_left = self.api.motor_l
            u_right = self.api.motor_r

        # 状態更新
        self.robot.update(u_left, u_right, self.dt)
        self._sim_time += self.dt
        
        # APIの状態を更新し、待機中のスレッドを起こす
        with self.api._lock :
            self.api.sim_time = self._sim_time
            self.api.line_sensors = self._line_sensor_values
            self.api.imu_yaw = self.imu.read_yaw(self.robot.theta)
            self.api._time_cond.notify_all()

    def run(self, auto_start=True) :
        # pygameウィンドウを開きシミュレーションを開始する
        pygame.init()

        self.course.load(self._course_path)
        self._renderer = Renderer(self.course)
        self.course.prepare()
        self._renderer.update_course_surface()

        # IMUとセンサの初期化
        self.imu.reset(self.robot.theta)
        self._read_sensors()

        print(f'[Simulator] Course: {self.course.pixel_width}x{self.course.pixel_height} px')
        print(f'[Simulator] Robot pose: ({self.robot.x:.1f}, {self.robot.y:.1f}, {self.robot.theta:.3f} rad)')
        print(f'[Simulator] Sensor values: {[f"{v:.2f}" for v in self._line_sensor_values]}')
        
        if self._start_user_thread() :
            print('[Simulator] Running in MICROCONTROLLER mode')

        if auto_start :
            self._running = True

        clock = pygame.time.Clock()
        frame_count = 0

        while True :
            if not self._handle_events() :
                self._quit()
                return

            if self._running and self._controller_fn :
                steps = max(1, int(self.speed_multiplier / self.fps / self.dt))

                for _ in range(steps) :
                    self._step_simulation()

                frame_count += 1
                if frame_count % 60 == 0 :
                    print(f'[Sim] t={self._sim_time:.2f}s  '
                          f'pos=({self.robot.x:.1f},{self.robot.y:.1f})  '
                          f'v={self.robot.v:.1f}  '
                          f'line={[f"{v:.2f}" for v in self._line_sensor_values]}  '
                          f'imu={self.imu.read_yaw(self.robot.theta):.2f}')

            # 描画
            imu_yaw = self.api.get_imu_yaw()
            self._renderer.draw(self.robot, self.line_sensor, self._line_sensor_values,
                                self._sim_time, self.speed_multiplier,
                                self._running, imu_yaw)

            clock.tick(self.fps)

    def _quit(self) :
        # アプリ終了時にユーザースレッドがブロックしていれば解放する
        with self.api._lock :
            self.api._quit = True
            self.api._time_cond.notify_all()
        pygame.quit()
