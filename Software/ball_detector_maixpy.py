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
uart = UART(UART.UART1, 115200, 8, 1, 0, timeout=1000, read_buf_len=4096)

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

# find_blobs用パラメータ (ROI絞り込み用)
BLOB_AREA_MIN = 100       # blobの最小面積 (これ以下は無視)
ROI_MARGIN = 5            # blob外接矩形に加えるマージン (px)

# 検出パラメータ (find_circles用)
CIRCLE_THRESHOLD = 4200   # ハフ変換の投票閾値 (小さいほど多く検出、大きいほど厳選)
R_MIN = 20                # 検出する最小半径 (px)
R_MAX = 80                # 検出する最大半径 (px)
R_STEP = 2                # 半径の探索ステップ
X_STRIDE = 2              # x方向の探索ステップ (大きいほど高速・低精度)
Y_STRIDE = 2              # y方向の探索ステップ

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
SHOW_BINARY = False       # 二値化マスクを表示 (Trueで元映像を二値化に置換)
BINARY_COLORS = ['red', 'yellow', 'blue']  # 二値化対象の色 (SHOW_BINARY=True時)
SHOW_BLOBS = False        # blob外接矩形を描画
SHOW_ROI = False          # ROI矩形 (マージン付き) を描画
SHOW_CIRCLES = True       # 検出した円を描画
SHOW_PRINT = True         # 検出結果をシリアル出力


def _clamp_roi(x, y, w, h, img_w, img_h) :
    # ROIを画像範囲内にクランプする
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(img_w, x + w)
    y2 = min(img_h, y + h)
    return (x1, y1, x2 - x1, y2 - y1)


def detect(img, extra_fb, color_name='red') :
    # 指定色のボールを検出する
    # 1. find_blobsで色領域を高速に検出
    # 2. 各blobの外接矩形(+マージン)をROIとしてfind_circlesを実行
    # img: sensor.snapshot() で取得した画像オブジェクト
    # extra_fb: 二値化用の事前確保バッファ
    # color_name: COLOR_THRESHOLDSのキー名
    # 戻り値: (results, blobs)
    #   results: [{'cx','cy','radius','magnitude'}, ...]
    #   blobs: find_blobsの結果 (描画用)
    thresh = COLOR_THRESHOLDS[color_name]
    img_w, img_h = img.width(), img.height()

    # ステップ1: 元画像でfind_blobs (色領域を高速に検出)
    blobs = img.find_blobs(
        [thresh],
        area_threshold=BLOB_AREA_MIN,
        pixels_threshold=BLOB_AREA_MIN,
        merge=True,
        margin=10,
    )

    if not blobs :
        return [], []

    # ステップ2: 二値化画像を準備
    extra_fb.draw_image(img, 0, 0)
    extra_fb.binary([thresh])

    # ステップ2.5: モルフォロジー処理 (opening: erode→dilate でノイズ除去)
    extra_fb.erode(1)
    extra_fb.dilate(1)

    # ステップ3: 各blobのROI内でfind_circles
    results = []
    for b in blobs :
        # blob外接矩形にマージンを加えてROIを設定
        roi = _clamp_roi(
            b.x() - ROI_MARGIN,
            b.y() - ROI_MARGIN,
            b.w() + ROI_MARGIN * 2,
            b.h() + ROI_MARGIN * 2,
            img_w, img_h,
        )

        # ROIが小さすぎる場合はスキップ
        if roi[2] < R_MIN * 2 or roi[3] < R_MIN * 2 :
            continue

        circles = extra_fb.find_circles(
            roi=roi,
            threshold=CIRCLE_THRESHOLD,
            x_margin=20,
            y_margin=20,
            r_margin=10,
            r_min=R_MIN,
            r_max=min(R_MAX, roi[2] // 2, roi[3] // 2),
            r_step=R_STEP,
            x_stride=X_STRIDE,
            y_stride=Y_STRIDE,
        )

        for c in circles :
            results.append({
                'cx': c.x(),
                'cy': c.y(),
                'radius': c.r(),
                'magnitude': c.magnitude(),
            })

    return results, blobs


# ============================================================
# メインループ
# ============================================================
lcd.init(freq=15000000)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320x240
sensor.skip_frames(time=2000)

# 二値化用バッファを初回コピーで確保 (以降はdraw_imageで上書き、GC負荷なし)
extra_fb = sensor.snapshot().copy()

clock = time.clock()

while True :
    clock.tick()
    img = sensor.snapshot()

    # DETECT_COLORSで指定した色のみ検出
    for color_name in DETECT_COLORS :
        results, blobs = detect(img, extra_fb, color_name)
        draw_color = DRAW_COLORS.get(color_name, (0, 255, 0))
        img_w, img_h = img.width(), img.height()

        # blob外接矩形を描画
        if SHOW_BLOBS :
            for b in blobs :
                img.draw_rectangle(b.rect(), color=draw_color, thickness=1)

        # ROI矩形を描画
        if SHOW_ROI :
            for b in blobs :
                roi = _clamp_roi(
                    b.x() - ROI_MARGIN, b.y() - ROI_MARGIN,
                    b.w() + ROI_MARGIN * 2, b.h() + ROI_MARGIN * 2,
                    img_w, img_h,
                )
                img.draw_rectangle(roi, color=(255, 255, 255), thickness=1)

        # 検出円を描画
        if SHOW_CIRCLES :
            for r in results :
                cx, cy, rad = r['cx'], r['cy'], r['radius']
                img.draw_circle(cx, cy, rad, color=draw_color, thickness=2)
                img.draw_cross(cx, cy, size=5, color=draw_color, thickness=1)

        # シリアル出力およびUART送信
        if SHOW_PRINT :
            #print('---\n')
            #uart.write('---\n') # 区切りも送信したい場合はコメントアウトを外す
            for r in results :
                # 送信用文字列を生成 (末尾に改行コード付与)
                msg = '%s: cx=%d cy=%d r=%d mag=%d\n' % (
                    color_name, r['cx'], r['cy'], r['radius'], r['magnitude'])
                print(msg.strip())  # REPLへの出力用
                uart.write(msg)     # UART経由での送信


    # 二値化マスク表示 (元映像を上書き)
    if SHOW_BINARY :
        thresh_list = [COLOR_THRESHOLDS[c] for c in BINARY_COLORS if c in COLOR_THRESHOLDS]
        if thresh_list :
            img.binary(thresh_list)

    lcd.display(img)
