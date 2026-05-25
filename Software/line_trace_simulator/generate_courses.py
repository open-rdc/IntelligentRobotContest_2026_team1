# サンプルコース画像を生成するスクリプト
# 使い方: python generate_courses.py
import pygame
import math
import os

# 出力先ディレクトリ
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'courses')


def generate_simple_oval(width=800, height=600, line_width=20) :
    # 単純な楕円コース（ライン幅を太くして検出しやすくする）
    surface = pygame.Surface((width, height))
    surface.fill((255, 255, 255))

    cx, cy = width // 2, height // 2
    rx, ry = 250, 180

    # 楕円を点列で描画
    points = []
    steps = 720
    for i in range(steps + 1) :
        angle = 2 * math.pi * i / steps
        x = cx + rx * math.cos(angle)
        y = cy + ry * math.sin(angle)
        points.append((x, y))

    pygame.draw.lines(surface, (0, 0, 0), True, points, line_width)

    return surface


def generate_figure_eight(width=800, height=600, line_width=20) :
    # 8の字コース
    surface = pygame.Surface((width, height))
    surface.fill((255, 255, 255))

    r = 150
    cx = width // 2
    cy = height // 2
    offset = r

    # 左の円
    steps = 360
    points_left = []
    for i in range(steps + 1) :
        angle = 2 * math.pi * i / steps
        x = cx - offset + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points_left.append((x, y))

    # 右の円
    points_right = []
    for i in range(steps + 1) :
        angle = 2 * math.pi * i / steps
        x = cx + offset + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points_right.append((x, y))

    if len(points_left) > 1 :
        pygame.draw.lines(surface, (0, 0, 0), True, points_left, line_width)
    if len(points_right) > 1 :
        pygame.draw.lines(surface, (0, 0, 0), True, points_right, line_width)

    return surface


def main() :
    pygame.init()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    courses = {
        'simple_oval.png': generate_simple_oval,
        'figure_eight.png': generate_figure_eight,
    }

    for filename, gen_func in courses.items() :
        surface = gen_func()
        path = os.path.join(OUTPUT_DIR, filename)
        pygame.image.save(surface, path)
        print(f'Generated: {path}')

    pygame.quit()
    print('Done.')


if __name__ == '__main__' :
    main()
