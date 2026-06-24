# Software

ロボット設計製作論実習4で使用するソフトウェア一式。

## ディレクトリ構成

```
├── components/              コンポーネントごとのドライバ群
│   ├── actuators/           アクチュエータ系 (motor, servo)
│   ├── api/                 ロボット制御API (robot_api)
│   ├── common/              共通データ構造 (sensor_data)
│   ├── sensors/             センサ系 (bno055, camera, color, line)
│   └── utils/               ユーティリティ (logger)
│
├── contest/                 コンテスト本番用プログラム
│   ├── src/                 メインロジックなど
│   │   └── main.c
│   └── CMakeLists.txt
│
├── rp2040_test/             センサ動作確認用テストプログラム
│   ├── rp2040_test.c
│   └── CMakeLists.txt
│
├── line_trace_simulator/    ライントレースシミュレータ (Python)
│
└── ball_detector_maixpy.py  UnitV用ボール検出プログラム (MaixPy)
```

## components - ドライバ群

`contest` などのプロジェクトで使用されるハードウェアドライバ。
`sensors/` フォルダにはセンサ類、`actuators/` フォルダにはモータ類が配置されています。

### ピンアサイン

| ピン | 機能 | 接続先 | ドライバ |
|------|------|--------|----------|
| GP0 | UART0 TX | (未使用) | camera |
| GP1 | UART0 RX | UnitV TX (Pin35) | camera |
| GP4 | PWM (CH B) | 右モータドライバ IN2 | motor |
| GP5 | PWM (CH A) | 右モータドライバ IN1 | motor |
| GP6 | I2C1 SDA | BNO055 SDA | bno055 |
| GP7 | I2C1 SCL | BNO055 SCL | bno055 |
| GP8 | PWM (CH A) | 左モータドライバ IN1 | motor |
| GP9 | PWM (CH B) | 左モータドライバ IN2 | motor |
| GP16 | GPIO OUT | マルチプレクサ S1 | line_sensor |
| GP17 | GPIO OUT | マルチプレクサ S0 | line_sensor |
| GP18 | PWM | サーボモータ | servo |
| GP26 | ADC0 | ラインセンサ アナログ入力 | line_sensor |
| GP27 | ADC1 | カラーセンサ Blue | color_sensor |
| GP28 | ADC2 | カラーセンサ Green | color_sensor |
| GP29 | ADC3 | カラーセンサ Red | color_sensor |

### Robot API

`robot_api.h` は、シミュレータ (`line_trace_simulator`) の `RobotAPI` (Python) に対応するC版APIである。
シミュレータとほぼ同じインターフェースで実機の制御コードを記述できる。

#### 初期化

```c
#include "robot_api.h"

int main() {
    robot_init();  // 全ハードウェアの初期化 (I2C, ADC, PWM, UART)
    // ...
}
```

`robot_init()` は以下を内部で実行する:
- `stdio_init_all()`
- 各センサ・アクチュエータの初期化 (`camera_init`, `line_sensor_init`, `motor_init`, etc.)
- I2C1の初期化 (GP6/GP7, 400kHz)
- BNO055の初期化 (NDOFモード)

#### モータ制御

```c
// 左右のモータ出力を設定 (-100.0 ~ 100.0)
// 正の値で前進方向、負の値で後退方向
robot_set_motor(60.0f, 60.0f);   // 前進
robot_set_motor(-50.0f, 50.0f);  // 左旋回
robot_set_motor(0.0f, 0.0f);     // 停止
```

#### 待機

```c
// 指定ミリ秒の待機
// 待機中もカメラのUART受信を内部で処理する
robot_wait_ms(100);
```

#### センサ読み取り

```c
// ラインセンサ (4ch, 0~100の正規化済み値)
uint16_t line[4];
robot_get_line_sensors(line);

// IMUのヨー角 [deg]
float yaw = robot_get_imu_yaw();

// IMUのヨー角を現在の姿勢で0にリセット
robot_reset_imu();

// カラーセンサ (B, G, R の順, ADC生値)
uint16_t color[3];
robot_get_color_sensor(color);

// カメラの検出結果 (UnitVからのUART受信データ)
// 戻り値: 値の個数 (0 = 前回取得時から更新なし)
int cam[16];
int count = robot_get_camera(cam, 16);

// 経過時間 [ms]
uint32_t now = robot_get_time_ms();
```

#### サーボ操作

```c
robot_servo_push();    // ボール押し出し
robot_servo_return();  // サーボ戻し
```

#### シミュレータとの対応表

| Python (シミュレータ) | C (robot_api) | 備考 |
|---|---|---|
| `robot.start_motor(l, r)` | `robot_set_motor(l, r)` | Python: -1.0~1.0 / C: -100.0~100.0 |
| `robot.wait(seconds)` | `robot_wait_ms(ms)` | Python: 秒 / C: ミリ秒 |
| `robot.get_line_sensors()` | `robot_get_line_sensors(out)` | Python: 0.0~1.0 / C: 0~100 |
| `robot.get_imu_yaw()` | `robot_get_imu_yaw()` | 共に度数法 [deg] |
| `robot.reset_imu()` | `robot_reset_imu()` | |

### 使用例: ライントレース

```c
#include "robot_api.h"

void main_control(void) {
    while (1) {
        uint16_t line[4];
        robot_get_line_sensors(line);

        float error = (float)line[1] - (float)line[2];
        float base = 60.0f;
        float kp = 0.5f;

        robot_set_motor(base - kp * error, base + kp * error);
        robot_wait_ms(10);
    }
}

int main() {
    robot_init();
    main_control();
    return 0;
}
```

### PWM仕様

| 対象 | 周波数 | Wrap値 | Duty計算 |
|------|--------|--------|----------|
| DCモータ | 40 kHz | 3124 (PWM_WRAP - 1) | `duty = wrap * (speed / 100)` |
| サーボ | 50 Hz | 20000 | パルス幅 500~2500 us |

## contest

コンテスト本番用プログラム。`robot_api` を使用して制御を記述する。

### ビルド

```bash
cd contest
mkdir build && cd build
cmake ..
make -j4
```

生成された `contest.uf2` をBOOTSELモードのRP2040にドラッグ&ドロップ。

## rp2040_test

全センサの動作確認用テストプログラム。`robot_api` を使用してセンサ値を100ms周期でシリアル出力する。

### ビルド

```bash
cd rp2040_test
mkdir build && cd build
cmake ..
make -j4
```

生成された `rp2040_test.uf2` をBOOTSELモードのRP2040にドラッグ&ドロップ。

### シリアルモニタ

```bash
ls /dev/cu.usbmodem*
screen /dev/cu.usbmodem* 115200  # 終了: Ctrl+A → K → Y
```

## ball_detector_maixpy.py

UnitV (M5Stack UnitV / K210) 上で動作するボール検出プログラム。

- **検出方式**: find_blobs → ROI絞り込み → find_circles (ハフ変換)
- **対応色**: 赤・黄・青 (LAB色空間の閾値で設定)
- **出力**: UART1 (TX=Pin35, 115200bps) で検出結果を送信
- **フォーマット**: `色ID cx cy r mag\n` (スペース区切り, 色ID: 1=赤, 2=黄, 3=青)

## line_trace_simulator

Pythonベースのライントレースシミュレータ。詳細は [line_trace_simulator/](line_trace_simulator/) を参照。
