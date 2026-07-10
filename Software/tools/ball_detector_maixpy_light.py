import sensor, image, lcd, time
from machine import UART
from fpioa_manager import fm

# ============================================================
# UART設定 (MaixPy / K210用)
# ============================================================
# UARTに使用するピン番号 (環境に合わせて変更してください)
# 一般的なUnitVのGroveポートの場合: TX=35, RX=34
UART_TX_PIN = 35
UART_RX_PIN = 34

fm.register(UART_TX_PIN, fm.fpioa.UART1_TX, force=True)
fm.register(UART_RX_PIN, fm.fpioa.UART1_RX, force=True)
uart = UART(UART.UART1, 115200, 8, 0, 1, timeout=1000, read_buf_len=4096)

# ============================================================
# 色閾値プリセット (MaixPy LABスケール: L=0-100, A=-128~127, B=-128~127)
# PC版 (OpenCV) からの変換式:
#   L_maixpy = L_cv * 100 / 255
#   A_maixpy = A_cv - 128
#   B_maixpy = B_cv - 128
# ============================================================
COLOR_THRESHOLDS = {
    #                 (L_min, L_max, A_min, A_max, B_min, B_max)
    'red':    (5,  100,  10,  127,   0,  127),
    'yellow': (20, 100, -30,   20,  30,  127),
    'blue':   (5,  100, -20,   70, -128, -28),
}

# find_blobs用パラメータ
BLOB_AREA_MIN = 100       # blobの最小面積 (これ以下は無視)

# 誤認識を防ぐための真円度チェック用（縦横比）
# 縦横比(幅/高さ)がこの範囲外なら、円ではない（細長いゴミなど）として弾く
RATIO_MIN = 0.67
RATIO_MAX = 1.5

# 面積比（実際のピクセル数 / 外接矩形の面積）のチェック用
# 真円の場合、面積比は π/4 ≒ 0.785 になる（四角形なら1.0に近い）
AREA_RATIO_MIN = 0.60
AREA_RATIO_MAX = 0.95

# 検出するボールの半径の制限 (px)
# この範囲外のサイズのボールは無視する
R_MIN = 30
R_MAX = 60

# 色ごとの描画色 (RGB)
DRAW_COLORS = {
    'red':    (255, 0, 0),
    'yellow': (255, 255, 0),
    'blue':   (0, 0, 255),
}

# ============================================================
# 表示設定 (それぞれ独立してON/OFF可能)
# ============================================================
DETECT_COLORS = ['red', 'yellow', 'blue']  # 検出対象の色
SHOW_BLOBS = True         # blob外接矩形を描画
SHOW_CIRCLES = True       # blobから推定した円を描画
SHOW_PRINT = True         # 検出結果をシリアル出力


def detect(img, color_name='red') :
    # 指定色のボールをfind_blobsのみで高速に検出する
    thresh = COLOR_THRESHOLDS[color_name]

    blobs = img.find_blobs(
        [thresh],
        area_threshold=BLOB_AREA_MIN,
        pixels_threshold=BLOB_AREA_MIN,
        merge=True,
        margin=10,
    )

    results = []
    valid_blobs = []

    if not blobs :
        return results, valid_blobs

    for b in blobs :
        # 縦横比を計算して細長いゴミや壁を弾く
        ratio = b.w() / float(b.h())
        if ratio < RATIO_MIN or ratio > RATIO_MAX :
            continue

        # 面積比を計算して、四角形（1.0に近い）やスカスカな図形を弾く
        area_ratio = b.pixels() / float(b.w() * b.h())
        if area_ratio < AREA_RATIO_MIN or area_ratio > AREA_RATIO_MAX :
            continue

        # 外接矩形の幅と高さの平均から半径を算出
        r = (b.w() + b.h()) // 4

        # 半径が指定範囲外のものは弾く
        if r < R_MIN or r > R_MAX :
            continue

        valid_blobs.append(b)

        results.append({
            'cx': b.cx(),
            'cy': b.cy(),
            'radius': r,
            'magnitude': int(area_ratio / 0.785 * 100),
        })

    return results, valid_blobs


# ============================================================
# メインループ
# ============================================================
lcd.init(freq=15000000)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320x240
sensor.skip_frames(time=2000)

clock = time.clock()

while True :
    clock.tick()
    img = sensor.snapshot()

    # すべての検出結果をまとめるリスト
    all_results = []

    # DETECT_COLORSで指定した色のみ検出
    for color_name in DETECT_COLORS :
        results, blobs = detect(img, color_name)
        draw_color = DRAW_COLORS.get(color_name, (0, 255, 0))

        # blob外接矩形を描画
        if SHOW_BLOBS :
            for b in blobs :
                img.draw_rectangle(b.rect(), color=draw_color, thickness=1)

        # 検出円を描画
        if SHOW_CIRCLES :
            for r in results :
                cx, cy, rad = r['cx'], r['cy'], r['radius']
                img.draw_circle(cx, cy, rad, color=draw_color, thickness=2)
                img.draw_cross(cx, cy, size=5, color=draw_color, thickness=1)

        # 検出結果をリストに追加
        color_map = {'red': 1, 'yellow': 2, 'blue': 3}
        color_id = color_map.get(color_name, 0)
        for r in results :
            all_results.append((color_id, r['cx'], r['cy'], r['radius'], r['magnitude']))

    # シリアル出力およびUART送信 (全色分を1行にまとめて送信)
    if SHOW_PRINT :
        if not all_results:
            # ボールが1つも検出されなかった場合
            msg = "0\n"
        else:
            # 複数ボールをスペース区切りで連結
            parts = ["%d %d %d %d %d" % res for res in all_results]
            msg = " ".join(parts) + "\n"

        print(msg.strip())  # REPLへの出力用
        uart.write(msg)     # UART経由での送信

    lcd.display(img)
