# ライントレースシミュレータ

Python + pygame によるライントレースロボットシミュレータ。
対向二輪ロボットのライントレース動作をシミュレーション・可視化します。

## セットアップ

```bash
pip install pygame

# (オプション) より正確なセンサの光量減衰シミュレーションを行う場合
pip install numpy
```

## クイックスタート

```bash
# サンプルコース画像を生成
python generate_courses.py

# P制御サンプルを実行
python examples/p_control.py
```

## 使い方

シミュレータへの制御プログラムは、1つの引数 (`robot`) を受け取る関数として定義します。
プログラムは別スレッドで実行され、マイコンのように逐次的な制御を書くことができます。

```python
from simulator import Simulator

def main_task(robot) :
    # 0.5秒間まっすぐ前進
    robot.start_motor(0.5, 0.5)
    robot.wait(0.5)
    
    # 停止して1秒待つ
    robot.start_motor(0, 0)
    robot.wait(1.0)
    
    # センサ値を使った制御ループ
    while True :
        line_sensors = robot.get_line_sensors()
        if line_sensors[1] < 0.5 :
            robot.start_motor(0.3, 0.5)
        else :
            robot.start_motor(0.5, 0.3)
        robot.wait(0.001)  # 1msの待機

sim = Simulator('courses/simple_oval.png', controller_fn=main_task)
sim.set_robot_pose(400, 120, 1.57)
sim.run()
```

**マイコン方式で利用できる主なAPI:**
- `robot.start_motor(left, right)`: 左右のモータの出力を設定します（-1.0～1.0）
- `robot.wait(seconds)`: 指定したシミュレーション時間（秒）だけ待機します
- `robot.get_line_sensors()`: 各ラインセンサの値のリストを取得します
- `robot.get_imu_yaw()`: 仮想IMUのヨー角を取得します（初期位置またはリセット時を0度とする）
- `robot.reset_imu()`: 現在の姿勢角を0度としてIMUをリセットします


## キー操作

| キー | 機能 |
|------|------|
| `Space` | 開始/停止 |
| `R` | リセット（制御プログラムも最初から実行し直されます） |
| `↑` / `↓` | 速度倍率の変更 |
| `T` | 軌跡表示ON/OFF |
| `ESC` | 終了 |

## パラメータ調整

```python
# ロボットパラメータ
sim.set_robot_params(
    track_width=100,      # 車輪間距離 [mm]
    wheel_radius=20,      # 車輪半径 [mm]
    max_motor_speed=10,   # 最大モータ角速度 [rad/s]
)

# ラインセンサパラメータ
sim.set_line_sensor_params(
    forward_offset=72.0,  # 前方オフセット [mm]
    offsets=[-20.1, -10.5, 10.5, 20.1],  # 各センサの横方向オフセット（不等間隔配置） [mm]
    fov_radius=2.6,       # 視野半径 [mm]
    sensor_height=5.0,    # センサの床面からの高さ [mm]
    half_angle=30.0,      # センサ光の半減角 [deg]
    noise_std=0.0,        # ノイズ強度
)

# 仮想IMUパラメータ
sim.set_imu_params(
    noise_std=0.01,       # ノイズ強度
)
```

## ファイル構成

```
line_trace_simulator/
├── simulator/          # シミュレータパッケージ
│   ├── __init__.py
│   ├── course.py       # コースモデル
│   ├── robot.py        # ロボットモデル（対向二輪）
│   ├── line_sensor.py  # ラインセンサモデル
│   ├── imu.py          # 仮想IMUモデル
│   ├── robot_api.py    # マイコン風APIモデル
│   ├── engine.py       # シミュレーションエンジン
│   └── renderer.py     # pygame描画
├── courses/            # コース画像
├── examples/           # サンプルプログラム
├── generate_courses.py # コース画像生成スクリプト
├── requirements.txt
└── README.md
```
