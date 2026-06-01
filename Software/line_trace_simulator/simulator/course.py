import pygame
import math

# numpyはオプション（あれば高速化に使用）
try :
    import numpy as np
    HAS_NUMPY = True
except ImportError :
    HAS_NUMPY = False


class CourseModel :
    # コース画像を管理し、任意座標の明度を返す

    def __init__(self, scale=1.0) :
        # scale: 1ピクセルあたりの実寸 [mm/px]（デフォルト: 1.0 = 1px=1mm）
        self.scale = scale
        self.surface = None
        self._pixel_array = None  # numpy配列（高速アクセス用）
        self._width = 0
        self._height = 0

    def load(self, image_path) :
        # コース画像を読み込む（display初期化前でも可）
        self.surface = pygame.image.load(image_path)
        self._width = self.surface.get_width()
        self._height = self.surface.get_height()

    def prepare(self) :
        # display初期化後に呼び出す。convert()とピクセルキャッシュを行う
        self.surface = self.surface.convert()

        if HAS_NUMPY :
            # ピクセル配列をnumpyで取得し、グレースケール化してキャッシュ
            arr = pygame.surfarray.pixels3d(self.surface).copy()  # (W, H, 3)
            # ITU-R BT.601の輝度変換: Y = 0.299R + 0.587G + 0.114B
            self._pixel_array = (
                arr[:, :, 0] * 0.299
                + arr[:, :, 1] * 0.587
                + arr[:, :, 2] * 0.114
            ) / 255.0  # 0.0～1.0に正規化
        else :
            self._pixel_array = None

    def get_brightness(self, x, y) :
        # 実座標(mm)から明度を取得する (0.0=黒, 1.0=白)
        px = int(x / self.scale)
        py = int(y / self.scale)

        # 範囲外は白として返す
        if px < 0 or px >= self._width or py < 0 or py >= self._height :
            return 1.0

        if self._pixel_array is not None :
            return float(self._pixel_array[px, py])
        else :
            # numpyなし: pygameのget_atで取得
            r, g, b, _ = self.surface.get_at((px, py))
            return (r * 0.299 + g * 0.587 + b * 0.114) / 255.0

    def get_brightness_area(self, cx, cy, radius) :
        # 円形領域内の明度の平均値を返す（センサの視野に対応）
        px_cx = int(cx / self.scale)
        px_cy = int(cy / self.scale)
        px_r = max(1, int(radius / self.scale))

        total = 0.0
        count = 0
        r_sq = px_r * px_r

        for dx in range(-px_r, px_r + 1) :
            for dy in range(-px_r, px_r + 1) :
                if dx * dx + dy * dy > r_sq :
                    continue
                px = px_cx + dx
                py = px_cy + dy
                if px < 0 or px >= self._width or py < 0 or py >= self._height :
                    total += 1.0  # 範囲外は白
                elif self._pixel_array is not None :
                    total += float(self._pixel_array[px, py])
                else :
                    r, g, b, _ = self.surface.get_at((px, py))
                    total += (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
                count += 1

        return total / count if count > 0 else 1.0

    def get_brightness_kernel(self, cx, cy, kernel, px_r) :
        # カーネルを用いた加重平均で明度を取得する
        px_cx = int(cx / self.scale)
        px_cy = int(cy / self.scale)

        if HAS_NUMPY and isinstance(kernel, np.ndarray) and self._pixel_array is not None :
            x_min = px_cx - px_r
            x_max = px_cx + px_r + 1
            y_min = px_cy - px_r
            y_max = px_cy + px_r + 1

            if x_min >= 0 and x_max <= self._width and y_min >= 0 and y_max <= self._height :
                region = self._pixel_array[x_min:x_max, y_min:y_max]
                return float(np.sum(region * kernel))

        total_val = 0.0
        
        for dx in range(-px_r, px_r + 1) :
            for dy in range(-px_r, px_r + 1) :
                w = kernel[dx + px_r][dy + px_r]
                if w <= 0.0 :
                    continue
                
                px = px_cx + dx
                py = px_cy + dy
                
                if px < 0 or px >= self._width or py < 0 or py >= self._height :
                    val = 1.0
                elif self._pixel_array is not None :
                    val = float(self._pixel_array[px, py])
                else :
                    r, g, b, _ = self.surface.get_at((px, py))
                    val = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
                    
                total_val += val * w

        return total_val

    @property
    def width(self) :
        # コースの幅 [mm]
        return self._width * self.scale

    @property
    def height(self) :
        # コースの高さ [mm]
        return self._height * self.scale

    @property
    def pixel_width(self) :
        return self._width

    @property
    def pixel_height(self) :
        return self._height
