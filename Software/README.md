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
                              └──────────────┘
```

## ファイル構成

| パス | 説明 |
|------|------|
| `ball_detector_maixpy.py` | UnitV用ボール検出プログラム (MaixPy) |
| `rp2040_test/rp2040_test.c` | RP2040メインプログラム |
| `rp2040_test/bno055.h` | BNO055 IMUドライバ (ヘッダ) |
| `rp2040_test/bno055.c` | BNO055 IMUドライバ (実装) |
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

1. **UART受信**: UnitVからのボール検出結果をUART0 (GP0=TX, GP1=RX) で受信し、USBシリアル経由でPCに転送
2. **IMU読み取り**: BNO055からI2C1 (GP6=SDA, GP7=SCL) でオイラー角・線形加速度を100ms間隔で取得

### ピンアサイン

| ピン | 機能 | 接続先 |
|------|------|--------|
| GP0 | UART0 TX | (未使用) |
| GP1 | UART0 RX | UnitV TX (Pin35) |
| GP6 | I2C1 SDA | BNO055 SDA |
| GP7 | I2C1 SCL | BNO055 SCL |
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
=== RP2040 テスト (UART + BNO055) ===
BNO055: チップID確認OK (0xA0)
BNO055: 初期化完了 (NDOFモード)
BNO055 Euler: Y=45.3 R=1.2 P=-0.5  Accel: X=0.01 Y=-0.03 Z=0.02
UART0 -> PC : red: cx=160 cy=120 r=35 mag=5200
```
