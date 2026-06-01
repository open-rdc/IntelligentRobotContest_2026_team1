import math
import random


class LineSensorModel :
    # ラインセンサの配置と読み取りを管理する

    def __init__(self, count=4, forward_offset=72.0, spacing=10.0,
                 offsets=[-21/2-9.6, -21/2, 21/2, 21/2+9.6], fov_radius=2.6, noise_std=0.0,
                 sensor_height=5.0, half_angle=30.0) :
        # count: センサ数（offsetsが未指定の場合に使用）
        # forward_offset: ロボット中心からセンサ列までの前方距離 [mm]
        # spacing: 隣接センサ間の距離 [mm]（offsetsが未指定の場合に使用）
        # offsets: 各センサの横方向オフセットのリスト [mm]（左が負、右が正）
        #          指定時はcount/spacingより優先される
        #          例: [-21/2-9.6, -21/2, 21/2, 21/2+9.6] → 不等間隔4センサ
        # fov_radius: 各センサの視野半径 [mm]
        # noise_std: ガウシアンノイズの標準偏差
        # sensor_height: センサの床面からの高さ [mm]
        # half_angle: センサの半減角 [deg]
        self.forward_offset = forward_offset
        self.fov_radius = fov_radius
        self.noise_std = noise_std
        self.sensor_height = sensor_height
        self.half_angle = half_angle
        
        self._kernel = None
        self._kernel_scale = 0.0
        self._px_r = 0

        if offsets is not None :
            # 任意配置（不等間隔対応）
            self._offsets = list(offsets)
            self.count = len(self._offsets)
        else :
            # 等間隔配置
            self.count = count
            self._offsets = [
                (i - (count - 1) / 2.0) * spacing
                for i in range(count)
            ]

    def get_positions(self, robot_state) :
        # 各センサのワールド座標を返す
        x = robot_state['x']
        y = robot_state['y']
        theta_rad = math.radians(robot_state['theta'])
        cos_t = math.cos(theta_rad)
        sin_t = math.sin(theta_rad)

        positions = []
        for d in self._offsets :
            sx = x + self.forward_offset * cos_t - d * sin_t
            sy = y + self.forward_offset * sin_t + d * cos_t
            positions.append((sx, sy))
        return positions

    def _generate_kernel(self, scale) :
        try :
            import numpy as np
            HAS_NUMPY = True
        except ImportError :
            HAS_NUMPY = False

        self._px_r = max(1, int(self.fov_radius / scale))
        size = 2 * self._px_r + 1

        half_angle_rad = math.radians(self.half_angle)
        cos_half = math.cos(half_angle_rad)
        if cos_half >= 1.0 or cos_half <= 0.0 :
            n_power = 1.0
        else :
            n_power = math.log(0.5) / math.log(cos_half)

        h = self.sensor_height / scale
        h_sq = h * h

        if HAS_NUMPY :
            kernel = np.zeros((size, size))
            total_weight = 0.0
            r_sq_max = self._px_r * self._px_r
            for dx in range(-self._px_r, self._px_r + 1) :
                for dy in range(-self._px_r, self._px_r + 1) :
                    r_sq = dx * dx + dy * dy
                    if r_sq <= r_sq_max :
                        cos_theta = h / math.sqrt(r_sq + h_sq)
                        w = math.pow(cos_theta, n_power)
                        kernel[dx + self._px_r, dy + self._px_r] = w
                        total_weight += w
            if total_weight > 0 :
                kernel /= total_weight
            self._kernel = kernel
        else :
            kernel = [[0.0 for _ in range(size)] for _ in range(size)]
            total_weight = 0.0
            r_sq_max = self._px_r * self._px_r
            for dx in range(-self._px_r, self._px_r + 1) :
                for dy in range(-self._px_r, self._px_r + 1) :
                    r_sq = dx * dx + dy * dy
                    if r_sq <= r_sq_max :
                        cos_theta = h / math.sqrt(r_sq + h_sq)
                        w = math.pow(cos_theta, n_power)
                        kernel[dx + self._px_r][dy + self._px_r] = w
                        total_weight += w
            if total_weight > 0 :
                for i in range(size) :
                    for j in range(size) :
                        kernel[i][j] /= total_weight
            self._kernel = kernel
            
        self._kernel_scale = scale

    def read(self, robot_state, course) :
        # センサ値を取得する
        if self._kernel is None or self._kernel_scale != course.scale :
            self._generate_kernel(course.scale)

        positions = self.get_positions(robot_state)
        values = []

        for sx, sy in positions :
            if self.fov_radius <= 1.0 :
                # 視野が1px以下なら点サンプリング
                val = course.get_brightness(sx, sy)
            else :
                # カーネルによる加重平均
                if hasattr(course, 'get_brightness_kernel') :
                    val = course.get_brightness_kernel(sx, sy, self._kernel, self._px_r)
                else :
                    val = course.get_brightness_area(sx, sy, self.fov_radius)

            # ノイズ付加
            if self.noise_std > 0 :
                val += random.gauss(0, self.noise_std)
                val = max(0.0, min(1.0, val))

            values.append(val)

        return values
