# ライントレースシミュレータ

Python + pygame によるライントレースロボットシミュレータ。
対向二輪ロボットのライントレース動作をシミュレーション・可視化します。

## セットアップ

```bash
pip install pygame
```

## クイックスタート

```bash
# サンプルコース画像を生成
python generate_courses.py

# P制御サンプルを実行
python examples/p_control.py
```

## 使い方

シミュレータには、従来の「コールバック方式」と、新しく追加された「マイコン方式」の2つの記述方法があります。
制御関数の引数の数によって自動的に切り替わります。

### 1. マイコン方式（おすすめ）
関数が1つの引数 (`robot`) を受け取る場合、プログラムは別スレッドで実行され、マイコンのように逐次的な制御を書くことができます。

```python
from simulator import Simulator

def main_task(robot) :
    # 0.5秒間まっすぐ前進
    robot.move_motor(0.5, 0.5)
    robot.wait(0.5)
    
    # 停止して1秒待つ
    robot.move_motor(0, 0)
    robot.wait(1.0)
    
    # センサ値を使った制御ループ
    while True :
        line_sensors = robot.get_line_sensors()
        if line_sensors[1] < 0.5 :
            robot.move_motor(0.3, 0.5)
        else :
            robot.move_motor(0.5, 0.3)
        robot.wait(0.001)  # 1msの待機

sim = Simulator('courses/simple_oval.png', controller_fn=main_task)
sim.set_robot_pose(400, 120, 1.57)
sim.run()
```

### 2. コールバック方式
関数が2つの引数 (`line_sensors`, `state`) を受け取る場合、毎ステップ（0.001秒ごと）に呼び出されます。

```python
from simulator import Simulator

def my_controller(line_sensors, state) :
    # line_sensors: 各ラインセンサのアナログ値 [0.0(黒)～1.0(白)] のリスト
    # state: {'x', 'y', 'theta', 'v', 'omega', 'time'}
    # 戻り値: (左モータ, 右モータ) 各 -1.0～1.0
    return (0.3, 0.3)

sim = Simulator('courses/simple_oval.png', controller_fn=my_controller)
sim.set_robot_pose(400, 120, 1.57)  # 初期位置
sim.run()
```

## キー操作

| キー | 機能 |
|------|------|
| `Space` | 開始/停止 |
| `R` | リセット |
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
    count=5,              # センサ数
    forward_offset=60,    # 前方オフセット [mm]
    spacing=10,           # センサ間隔 [mm]
    fov_radius=3,         # 視野半径 [mm]
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
