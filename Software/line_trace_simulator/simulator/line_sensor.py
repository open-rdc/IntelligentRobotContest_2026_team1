import math
import random


class LineSensorModel :
    # ラインセンサの配置と読み取りを管理する

    def __init__(self, count=4, forward_offset=90.0, spacing=10.0,
                 offsets=[-21/2-9.6, -21/2, 21/2, 21/2+9.6], fov_radius=2.0, noise_std=0.0) :
        # count: センサ数（offsetsが未指定の場合に使用）
        # forward_offset: ロボット中心からセンサ列までの前方距離 [mm]
        # spacing: 隣接センサ間の距離 [mm]（offsetsが未指定の場合に使用）
        # offsets: 各センサの横方向オフセットのリスト [mm]（左が負、右が正）
        #          指定時はcount/spacingより優先される
        #          例: [-21/2-9.6, -21/2, 21/2, 21/2+9.6] → 不等間隔4センサ
        # fov_radius: 各センサの視野半径 [mm]
        # noise_std: ガウシアンノイズの標準偏差
        self.forward_offset = forward_offset
        self.fov_radius = fov_radius
        self.noise_std = noise_std

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
        theta = robot_state['theta']
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        positions = []
        for d in self._offsets :
            sx = x + self.forward_offset * cos_t - d * sin_t
            sy = y + self.forward_offset * sin_t + d * cos_t
            positions.append((sx, sy))
        return positions

    def read(self, robot_state, course) :
        # センサ値を取得する
        # 戻り値: 各センサのアナログ値 (0.0=黒, 1.0=白) のリスト
        positions = self.get_positions(robot_state)
        values = []

        for sx, sy in positions :
            if self.fov_radius <= 1.0 :
                # 視野が1px以下なら点サンプリング
                val = course.get_brightness(sx, sy)
            else :
                # 視野半径内の平均明度
                val = course.get_brightness_area(sx, sy, self.fov_radius)

            # ノイズ付加
            if self.noise_std > 0 :
                val += random.gauss(0, self.noise_std)
                val = max(0.0, min(1.0, val))

            values.append(val)

        return values
