import random

class IMUModel :
    # 仮想IMUモデル（ヨー角の取得）

    def __init__(self, noise_std=0.0) :
        # noise_std: ガウシアンノイズの標準偏差 [deg]
        self.noise_std = noise_std
        self.offset = 0.0

    def reset(self, initial_theta) :
        # 基準となる角度をリセットする
        self.offset = initial_theta

    def read_yaw(self, true_theta) :
        # 真の角度(true_theta)からオフセットを引いたものにノイズを乗せて返す
        val = true_theta - self.offset
        if self.noise_std > 0 :
            val += random.gauss(0, self.noise_std)
        
        # 角度を[-180, 180]に正規化
        val = (val + 180.0) % 360.0 - 180.0
        return val
