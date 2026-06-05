# Software

ロボット設計製作論実習4で使用するソフトウェア一式。

## システム構成

```
UnitV (MaixPy/K210)          AE-RP2040                   PC
┌──────────────┐    UART     ┌──────────────┐    USB     ┌──────┐
│ ball_detector │──────────→│  rp2040_test  │──────────→│ 表示  │
│  カメラ+検出   │ TX35→GP1  │  統合制御     │  stdio    │      │
└──────────────┘  115200bps  │              │           └──────┘
                              │  BNO055 (I2C) │
                              │  GP6=SDA      │
                              │  GP7=SCL      │
                              │               │
                              │  Line Sensor  │
                              │  GP26=ADC0    │
                              │  GP16,17=MUX  │
                              └──────────────┘
```

## ファイル構成

| パス | 説明 |
|------|------|
| `ball_detector_maixpy.py` | UnitV用ボール検出プログラム (MaixPy) |
| `rp2040_test/rp2040_test.c` | RP2040メインプログラム |
| `rp2040_test/sensor_data.h` | センサデータ保持用構造体定義 |
| `rp2040_test/camera.c`, `.h` | UART経由のカメラデータ受信・パース |
| `rp2040_test/line_sensor.c`, `.h`| ライントレースセンサ用ADC制御・正規化 |
| `rp2040_test/bno055.c`, `.h` | BNO055 IMUドライバ |
| `rp2040_test/CMakeLists.txt` | RP2040ビルド設定 |

## ball_detector_maixpy.py

UnitV (M5Stack UnitV / K210) 上で動作するボール検出プログラム。

- **検出方式**: find_blobs → ROI絞り込み → find_circles (ハフ変換)
- **対応色**: 赤・黄・青 (LAB色空間の閾値で設定)
- **出力**: UART1 (TX=Pin35, RX=Pin34, 115200bps) で検出結果を送信
- **フォーマット**: `色名: cx=X cy=Y r=R mag=M\n`

## rp2040_test

AE-RP2040 (Pico SDK / C言語) 上で動作する統合制御プログラム。

### 機能

1. **カメラデータ受信**: UnitVからのカメラ検出結果(スペース区切り数値)をUART0 (GP0=TX, GP1=RX) で受信・パースし、整数配列として保持
2. **IMU読み取り**: BNO055からI2C1 (GP6=SDA, GP7=SCL) で姿勢データを定期取得
3. **ライントレースセンサ**: ADC0 (GP26) とマルチプレクサ (GP16, 17) を用いて、4ch分の反射光センサの値を定期取得し、0〜100に正規化
4. **統合出力**: 上記のデータを100ms周期で1行にまとめてUSBシリアル経由でPCに出力

### ピンアサイン

| ピン | 機能 | 接続先 |
|------|------|--------|
| GP0 | UART0 TX | (未使用) |
| GP1 | UART0 RX | UnitV TX (Pin35) |
| GP6 | I2C1 SDA | BNO055 SDA |
| GP7 | I2C1 SCL | BNO055 SCL |
| GP16 | GPIO OUT | マルチプレクサ S1 |
| GP17 | GPIO OUT | マルチプレクサ S0 |
| GP26 | ADC0 | ライントレースセンサ アナログ入力 |
| USB | stdio | PC (シリアルモニタ) |

### ビルド・書き込み

```bash
cd rp2040_test
mkdir build && cd build
cmake ..
make -j4
```

生成された `rp2040_test.uf2` をBOOTSELモードのRP2040にドラッグ&ドロップ。

### シリアルモニタ

```bash
# デバイス確認
ls /dev/cu.usbmodem*

# 接続 (終了: Ctrl+A → K → Y)
screen /dev/cu.usbmodem* 115200
```

### 出力例

```
=== RP2040 テスト (UART + BNO055 + Line) ===
BNO055: チップID確認OK (0xA0)
BNO055: 初期化完了 (NDOFモード)
Cam:[160 120 35 5200] BNO:[45.3] Line:[C0=  10 C1=  20 C2=  15 C3=  80]
Cam:[---] BNO:[45.4] Line:[C0=  10 C1=  21 C2=  15 C3=  82]
```
