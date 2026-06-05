import math

class RobotModel :
    # 対向二輪ロボットのキネマティクスモデル
    # モータの一次遅れ・不感帯にも対応

    def __init__(self, track_width=190.0, wheel_radius=35.0, max_motor_speed=10.0,
                 motor_tau=0.1, motor_deadzone=0.05) :
        # 200mm角・2kgロボットを想定したデフォルト値
        # track_width: 車輪間距離(トレッド) [mm]（車体幅200mmに対し左右20mmずつ内側）
        # wheel_radius: 車輪半径 [mm]（φ50mmホイール）
        # max_motor_speed: 最大モータ角速度 [rad/s]（ギヤ減速後、v_max = 25*20 = 500mm/s）
        # motor_tau: モータの一次遅れ時定数 [s]（0で遅れなし）
        #   小型DCモータ+ギヤボックスで50ms程度が典型
        # motor_deadzone: モータの不感帯 [0.0～1.0]（入力の絶対値がこれ以下なら出力0）
        #   静止摩擦やギヤのバックラッシュによる不感帯
        self.track_width = track_width
        self.wheel_radius = wheel_radius
        self.max_motor_speed = max_motor_speed
        self.motor_tau = motor_tau
        self.motor_deadzone = motor_deadzone

        # 状態変数
        self.x = 0.0       # 位置X [mm]
        self.y = 0.0       # 位置Y [mm]
        self.theta = 0.0   # 向き [deg] (X+が0、反時計回り正)
        self.v = 0.0       # 並進速度 [mm/s]
        self.omega = 0.0   # 旋回角速度 [deg/s]

        # モータの実際の角速度（一次遅れ適用後の値）
        self._motor_actual_l = 0.0
        self._motor_actual_r = 0.0

        # 初期位置の記憶（リセット用）
        self._init_x = 0.0
        self._init_y = 0.0
        self._init_theta = 0.0

    def set_pose(self, x, y, theta) :
        # 位置・姿勢を設定する
        self.x = x
        self.y = y
        self.theta = theta
        self._init_x = x
        self._init_y = y
        self._init_theta = theta

    def reset(self) :
        # 初期位置に戻す
        self.x = self._init_x
        self.y = self._init_y
        self.theta = self._init_theta
        self.v = 0.0
        self.omega = 0.0
        self._motor_actual_l = 0.0
        self._motor_actual_r = 0.0

    def _apply_deadzone(self, u) :
        if abs(u) <= self.motor_deadzone :
            return 0.0
        return (u - math.copysign(self.motor_deadzone, u)) / (1.0 - self.motor_deadzone)

    def update(self, u_left, u_right, dt) :
        u_left = max(-1.0, min(1.0, u_left))
        u_right = max(-1.0, min(1.0, u_right))

        u_left = self._apply_deadzone(u_left)
        u_right = self._apply_deadzone(u_right)

        cmd_l = u_left * self.max_motor_speed
        cmd_r = u_right * self.max_motor_speed

        if self.motor_tau > 0.0 :
            alpha = dt / (self.motor_tau + dt)
            self._motor_actual_l += alpha * (cmd_l - self._motor_actual_l)
            self._motor_actual_r += alpha * (cmd_r - self._motor_actual_r)
        else :
            self._motor_actual_l = cmd_l
            self._motor_actual_r = cmd_r

        v_l = self.wheel_radius * self._motor_actual_l
        v_r = self.wheel_radius * self._motor_actual_r

        self.v = (v_r + v_l) / 2.0
        omega_rad = (v_r - v_l) / self.track_width
        self.omega = math.degrees(omega_rad)

        theta_rad = math.radians(self.theta)
        self.x += self.v * math.cos(theta_rad) * dt
        self.y += self.v * math.sin(theta_rad) * dt
        self.theta += self.omega * dt

        self.theta = (self.theta + 180.0) % 360.0 - 180.0

    @property
    def state(self) :
        return {
            'x': self.x,
            'y': self.y,
            'theta': self.theta,
            'v': self.v,
            'omega': self.omega,
        }

    @property
    def wheel_positions(self) :
        # 左右車輪のワールド座標を返す（描画用）
        theta_rad = math.radians(self.theta)
        dx = (self.track_width / 2.0) * math.sin(theta_rad)
        dy = (self.track_width / 2.0) * math.cos(theta_rad)
        
        left_pos = (self.x + dx, self.y - dy)
        right_pos = (self.x - dx, self.y + dy)
        return left_pos, right_pos
