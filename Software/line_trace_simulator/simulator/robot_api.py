import threading


class RobotAPI :
    # 別スレッドで動くユーザープログラムとシミュレータを繋ぐAPI

    def __init__(self) :
        # 共有状態
        self.motor_l = 0.0
        self.motor_r = 0.0
        self.sim_time = 0.0
        self.line_sensors = []
        self.imu_yaw = 0.0
        self._imu_offset = 0.0
        
        # 同期用ロックと条件変数
        self._lock = threading.Lock()
        self._time_cond = threading.Condition(self._lock)
        self._quit = False
        self._resetting = False

    def _check_abort(self) :
        if self._quit or self._resetting :
            raise SystemExit("Simulation aborted or reset")

    # ===== ユーザー側API =====

    def move_motor(self, left, right) :
        # モータ出力を設定する（-1.0 ～ 1.0）
        with self._lock :
            self._check_abort()
            self.motor_l = left
            self.motor_r = right

    def wait(self, seconds) :
        # 指定秒数（シミュレーション時間）待機する
        with self._lock :
            self._check_abort()
            target_time = self.sim_time + seconds
            while self.sim_time < target_time :
                self._time_cond.wait()
                self._check_abort()

    def get_line_sensors(self) :
        # ラインセンサの最新値のリストを取得する
        with self._lock :
            self._check_abort()
            return list(self.line_sensors)

    def get_line_sensor(self, index) :
        # 指定したインデックスのラインセンサ値を取得する
        with self._lock :
            self._check_abort()
            if 0 <= index < len(self.line_sensors) :
                return self.line_sensors[index]
            return 1.0

    def reset_imu(self) :
        # IMUの角度を現在の姿勢を0としてリセットする
        with self._lock :
            self._imu_offset = self.imu_yaw

    def get_imu_yaw(self) :
        # IMUのヨー角（姿勢角）を取得する
        import math
        with self._lock :
            yaw = self.imu_yaw - self._imu_offset
            return math.atan2(math.sin(yaw), math.cos(yaw))
