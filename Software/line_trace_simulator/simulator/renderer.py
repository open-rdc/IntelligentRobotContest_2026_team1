import pygame
import math


# 配色
COLOR_BG = (32, 34, 37)
COLOR_PANEL_BG = (44, 47, 51)
COLOR_PANEL_HEADER = (55, 58, 63)
COLOR_TEXT = (215, 218, 220)
COLOR_TEXT_DIM = (140, 142, 145)
COLOR_TEXT_ACCENT = (114, 137, 218)
COLOR_DIVIDER = (65, 68, 74)
COLOR_ROBOT_BODY = (66, 133, 244)
COLOR_ROBOT_SHADOW = (40, 80, 150)
COLOR_ROBOT_OUTLINE = (52, 106, 195)
COLOR_WHEEL = (60, 63, 68)
COLOR_WHEEL_OUTLINE = (90, 93, 98)
COLOR_TRAIL = (66, 133, 244)
COLOR_RUNNING = (67, 181, 129)
COLOR_STOPPED = (240, 71, 71)
COLOR_BAR_BG = (32, 34, 37)
COLOR_BAR_BORDER = (55, 58, 63)

# コースの表示上限サイズ
MAX_CANVAS_W = 900
MAX_CANVAS_H = 750


def sensor_color(value) :
    # センサ値→色 (0.0=黒検出→赤, 1.0=白→緑)
    if value < 0.5 :
        t = value / 0.5
        r = int(240 * (1 - t) + 255 * t)
        g = int(71 * (1 - t) + 200 * t)
        b = int(71 * (1 - t) + 50 * t)
    else :
        t = (value - 0.5) / 0.5
        r = int(255 * (1 - t) + 67 * t)
        g = int(200 * (1 - t) + 181 * t)
        b = int(50 * (1 - t) + 129 * t)
    return (r, g, b)


class Renderer :
    # pygameによる描画（表示スケーリング対応）

    PANEL_WIDTH = 270

    def __init__(self, course) :
        self.course = course
        self.panel_width = self.PANEL_WIDTH

        # 表示スケールを計算（コースが大きい場合は縮小表示）
        src_w = course.pixel_width
        src_h = course.pixel_height
        scale_w = MAX_CANVAS_W / src_w if src_w > MAX_CANVAS_W else 1.0
        scale_h = MAX_CANVAS_H / src_h if src_h > MAX_CANVAS_H else 1.0
        self.view_scale = min(scale_w, scale_h)

        self.canvas_w = int(src_w * self.view_scale)
        self.canvas_h = int(src_h * self.view_scale)

        # スケーリング済みコース画像（update_course_surfaceで生成）
        self._course_scaled = None

        win_w = self.canvas_w + self.panel_width
        win_h = max(self.canvas_h, 750)
        self.screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption('Line Trace Simulator')

        print(f'[Renderer] Course: {src_w}x{src_h}px -> '
              f'Display: {self.canvas_w}x{self.canvas_h}px '
              f'(scale={self.view_scale:.3f})')

        # フォント
        self.font = pygame.font.SysFont('menlo', 13)
        self.font_bold = pygame.font.SysFont('menlo', 13, bold=True)
        self.font_title = pygame.font.SysFont('menlo', 14, bold=True)
        self.font_small = pygame.font.SysFont('menlo', 11)

        # 軌跡
        self.trail = []
        self.show_trail = True
        self.max_trail = 3000

        # FOV可視化用の半透明サーフェス
        self._fov_surface = pygame.Surface(
            (self.canvas_w, self.canvas_h), pygame.SRCALPHA)

    def update_course_surface(self) :
        # course.prepare()後に呼び出し、スケーリング済み描画用画像を生成する
        if self.view_scale < 1.0 :
            self._course_scaled = pygame.transform.smoothscale(
                self.course.surface, (self.canvas_w, self.canvas_h))
        else :
            self._course_scaled = self.course.surface

    # ===== 座標変換 =====

    def _to_screen(self, x, y) :
        # ワールド座標(mm) → 画面ピクセル座標に変換
        # CourseModelのscale(mm/px)と表示スケールの両方を適用
        scale = self.course.scale
        return (int(x / scale * self.view_scale),
                int(y / scale * self.view_scale))

    def _to_screen_len(self, length) :
        # ワールド座標での長さ → 画面ピクセル長に変換
        return length / self.course.scale * self.view_scale

    def clear_trail(self) :
        self.trail = []

    def draw(self, robot, line_sensor_model, line_sensor_values,
             sim_time, speed_mult, running, imu_yaw) :
        self.screen.fill(COLOR_BG)

        # コース描画（スケーリング済み画像）
        self.screen.blit(self._course_scaled, (0, 0))

        # 軌跡描画
        self._draw_trail()

        # ロボット描画
        self._draw_robot(robot, line_sensor_model, line_sensor_values)

        # 右パネル
        self._draw_panel(robot, line_sensor_model, line_sensor_values,
                         sim_time, speed_mult, running, imu_yaw)

        pygame.display.flip()

        # 軌跡追加（ワールド座標で保持）
        pos = (robot.x, robot.y)
        if not self.trail or self.trail[-1] != pos :
            self.trail.append(pos)
            if len(self.trail) > self.max_trail :
                self.trail.pop(0)

    def _draw_trail(self) :
        if not self.show_trail or len(self.trail) < 2 :
            return
        n = len(self.trail)
        step = max(1, n // 200)
        for i in range(0, n - 1, step) :
            p1 = self._to_screen(*self.trail[i])
            p2 = self._to_screen(*self.trail[min(i + step, n - 1)])
            pygame.draw.aaline(self.screen, COLOR_TRAIL, p1, p2)

    def _draw_sensor_fov(self, robot, line_sensor_model, line_sensor_values) :
        if not line_sensor_values :
            return
        self._fov_surface.fill((0, 0, 0, 0))
        positions = line_sensor_model.get_positions(robot.state)
        for i, (sx, sy) in enumerate(positions) :
            screen_pos = self._to_screen(sx, sy)
            r = max(2, int(self._to_screen_len(line_sensor_model.fov_radius)))
            color = (*sensor_color(line_sensor_values[i]), 50)
            pygame.draw.circle(self._fov_surface, color, screen_pos, r)
        self.screen.blit(self._fov_surface, (0, 0))

    def _draw_robot(self, robot, line_sensor_model, line_sensor_values) :
        scx, scy = self._to_screen(robot.x, robot.y)
        theta_rad = math.radians(robot.theta)
        cos_t = math.cos(theta_rad)
        sin_t = math.sin(theta_rad)

        body_w = self._to_screen_len(robot.track_width * 0.7)
        body_h = self._to_screen_len(robot.track_width * 0.9)
        hw, hh = body_w / 2, body_h / 2

        # 回転行列適用のヘルパー（画面座標系で計算）
        def rot(dx, dy) :
            return (scx + dx * (-sin_t) + dy * cos_t,
                    scy + dx * cos_t + dy * sin_t)

        # ---- 車輪 ----
        (lx, ly), (rx, ry) = robot.wheel_positions
        slx, sly = self._to_screen(lx, ly)
        srx, sry = self._to_screen(rx, ry)
        ww = self._to_screen_len(10)
        wh = self._to_screen_len(robot.wheel_radius * 1.6)
        for wx, wy in [(slx, sly), (srx, sry)] :
            wc = [(-ww/2, -wh/2), (ww/2, -wh/2),
                  (ww/2, wh/2), (-ww/2, wh/2)]
            wr = [(wx + dx*(-sin_t) + dy*cos_t,
                   wy + dx*cos_t + dy*sin_t) for dx, dy in wc]
            pygame.draw.polygon(self.screen, COLOR_WHEEL, wr)
            pygame.draw.polygon(self.screen, COLOR_WHEEL_OUTLINE, wr, 1)

        # ---- 本体（影 → 本体 → アウトライン） ----
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        so = 3
        shadow = [rot(dx + so * 0.3, dy + so * 0.3) for dx, dy in corners]
        pygame.draw.polygon(self.screen, (20, 20, 25), shadow)

        body = [rot(dx, dy) for dx, dy in corners]
        pygame.draw.polygon(self.screen, COLOR_ROBOT_BODY, body)
        pygame.draw.polygon(self.screen, COLOR_ROBOT_OUTLINE, body, 2)

        # ---- 前方向マーカー ----
        ab = body_h * 0.3
        al = body_h * 0.15
        a_tip = rot(0, hh + al * 0.3)
        a_left = rot(-ab * 0.3, hh - al * 0.5)
        a_right = rot(ab * 0.3, hh - al * 0.5)
        pygame.draw.polygon(self.screen, (255, 255, 255),
                            [a_tip, a_left, a_right])

        # ---- 中心マーカー ----
        pygame.draw.circle(self.screen, (255, 255, 255), (scx, scy), 3)
        pygame.draw.circle(self.screen, COLOR_ROBOT_OUTLINE, (scx, scy), 3, 1)

        # ---- センサ ----
        if line_sensor_values :
            positions = line_sensor_model.get_positions(robot.state)
            for i, (sx, sy) in enumerate(positions) :
                sp = self._to_screen(sx, sy)
                c = sensor_color(line_sensor_values[i])
                pygame.draw.circle(self.screen, (0, 0, 0), sp, 5)
                pygame.draw.circle(self.screen, c, sp, 4)
                pygame.draw.circle(self.screen, (255, 255, 255), sp, 4, 1)

    # ===== 右パネル描画 =====

    def _draw_panel(self, robot, line_sensor_model, line_sensor_values,
                    sim_time, speed_mult, running, imu_yaw) :
        px = self.canvas_w
        ph = self.screen.get_height()

        pygame.draw.rect(self.screen, COLOR_PANEL_BG,
                         pygame.Rect(px, 0, self.panel_width, ph))
        pygame.draw.line(self.screen, COLOR_DIVIDER,
                         (px, 0), (px, ph), 2)

        x = px + 14
        y = 10

        # ステータスヘッダ
        status_color = COLOR_RUNNING if running else COLOR_STOPPED
        status_text = 'RUNNING' if running else 'STOPPED'
        pygame.draw.circle(self.screen, status_color, (x + 6, y + 8), 5)
        st_surf = self.font_bold.render(status_text, True, status_color)
        self.screen.blit(st_surf, (x + 16, y))
        time_surf = self.font.render(f'{sim_time:.3f}s', True, COLOR_TEXT)
        self.screen.blit(time_surf, (x + 16 + st_surf.get_width() + 10, y))
        y += 24

        y = self._draw_divider(x - 4, y, self.panel_width - 20)

        y = self._draw_section(x, y, 'CONTROLS', [
            ('Space', 'Start / Stop'),
            ('R', 'Reset'),
            ('Up/Down', 'Speed'),
            ('T', 'Trail'),
            ('ESC', 'Quit'),
        ], key_value=True)

        y = self._draw_divider(x - 4, y, self.panel_width - 20)

        y = self._draw_section(x, y, 'ROBOT', [
            ('Pos', f'({robot.x:.1f}, {robot.y:.1f})'),
            ('Angle', f'{robot.theta:.1f} deg'),
            ('IMU Yaw', f'{imu_yaw:.1f} deg'),
            ('Speed', f'{robot.v:.1f} mm/s'),
            ('Omega', f'{robot.omega:.1f} deg/s'),
            ('Mult', f'{speed_mult:.1f}x'),
        ], key_value=True)

        y = self._draw_divider(x - 4, y, self.panel_width - 20)

        y = self._draw_section(x, y, 'PARAMS', [
            ('Track', f'{robot.track_width:.0f} mm'),
            ('Wheel', f'{robot.wheel_radius:.0f} mm'),
            ('Motor', f'{robot.max_motor_speed:.1f} rad/s'),
            ('Fwd', f'{line_sensor_model.forward_offset:.0f} mm'),
            ('FOV', f'{line_sensor_model.fov_radius:.0f} mm'),
        ], key_value=True)

        y = self._draw_divider(x - 4, y, self.panel_width - 20)

        y = self._draw_sensor_bars(x, y, line_sensor_model, line_sensor_values)

        y = self._draw_divider(x - 4, y, self.panel_width - 20)

        y = self._draw_magnifier(x, y, robot, line_sensor_model, line_sensor_values)

    def _draw_magnifier(self, x, y, robot, line_sensor_model, line_sensor_values) :
        ts = self.font_title.render('MAGNIFIER', True, COLOR_TEXT_ACCENT)
        self.screen.blit(ts, (x, y))
        y += 20

        disp_size = 180
        crop_size = 90
        margin_crop = int(crop_size * 1.5)
        
        scx, scy = self._to_screen(robot.x, robot.y)
        rect_x = int(scx - margin_crop / 2)
        rect_y = int(scy - margin_crop / 2)
        
        try:
            # 画面外の余白を持たせるため、一時Surfaceに描画
            src_surf = pygame.Surface((margin_crop, margin_crop))
            src_surf.fill(COLOR_BG)
            
            blit_x, blit_y = 0, 0
            src_x, src_y = rect_x, rect_y
            src_w, src_h = margin_crop, margin_crop
            
            if src_x < 0:
                blit_x = -src_x
                src_w += src_x
                src_x = 0
            if src_y < 0:
                blit_y = -src_y
                src_h += src_y
                src_y = 0
            if src_x + src_w > self.canvas_w:
                src_w = self.canvas_w - src_x
            if src_y + src_h > self.canvas_h:
                src_h = self.canvas_h - src_y
                
            if src_w > 0 and src_h > 0:
                src_surf.blit(self._course_scaled, (blit_x, blit_y), (src_x, src_y, src_w, src_h))
            
            # 回転: ロボット前方が上を向くように背景を逆回転
            angle = robot.theta + 90
            rotated_surf = pygame.transform.rotate(src_surf, angle)
            
            # 中央のクロップ
            rcx, rcy = rotated_surf.get_width() / 2, rotated_surf.get_height() / 2
            final_crop = rotated_surf.subsurface(pygame.Rect(int(rcx - crop_size/2), int(rcy - crop_size/2), crop_size, crop_size))
            
            # 拡大
            mag_bg = pygame.transform.scale(final_crop, (disp_size, disp_size))
            
            # ロボットとセンサの描画
            zoom = disp_size / crop_size
            cx, cy = disp_size / 2, disp_size / 2
            
            def to_mag_len(length):
                return self._to_screen_len(length) * zoom
            def local_to_mag(dx, dy):
                # dx: 右方, dy: 前方 -> Pygame(X:右, Y:下)
                return (cx + dx, cy - dy)
            
            # 車体サイズ
            body_w = to_mag_len(robot.track_width * 0.7 / 2) # X（右）方向
            body_h = to_mag_len(robot.track_width * 0.9 / 2) # Y（前）方向
            
            # 輪郭描画 (四隅: 右前、左前、左後、右後)
            corners = [
                local_to_mag(body_w, body_h),
                local_to_mag(-body_w, body_h),
                local_to_mag(-body_w, -body_h),
                local_to_mag(body_w, -body_h)
            ]
            pygame.draw.polygon(mag_bg, COLOR_ROBOT_OUTLINE, corners, 2)
            
            # 車輪
            ww = to_mag_len(10)
            wh = to_mag_len(robot.wheel_radius * 1.6)
            tw_half = to_mag_len(robot.track_width / 2)
            for wx in [tw_half, -tw_half]:
                wc = [
                    local_to_mag(wx + ww/2, wh/2),
                    local_to_mag(wx - ww/2, wh/2),
                    local_to_mag(wx - ww/2, -wh/2),
                    local_to_mag(wx + ww/2, -wh/2)
                ]
                pygame.draw.polygon(mag_bg, COLOR_WHEEL, wc)
                pygame.draw.polygon(mag_bg, COLOR_WHEEL_OUTLINE, wc, 1)
                
            # 前方マーカー
            a_tip = local_to_mag(0, body_h + body_h * 0.3)
            a_left = local_to_mag(-body_w * 0.3, body_h)
            a_right = local_to_mag(body_w * 0.3, body_h)
            pygame.draw.polygon(mag_bg, COLOR_ROBOT_OUTLINE, [a_tip, a_left, a_right], 1)
            
            # センサFOV
            if line_sensor_values:
                fov_r = max(2, int(to_mag_len(line_sensor_model.fov_radius)))
                fwd_off = to_mag_len(line_sensor_model.forward_offset)
                
                fov_surf = pygame.Surface((fov_r * 2, fov_r * 2), pygame.SRCALPHA)
                
                for i, d in enumerate(line_sensor_model._offsets):
                    dx = to_mag_len(d)
                    sp = local_to_mag(dx, fwd_off)
                    
                    c = sensor_color(line_sensor_values[i])
                    
                    fov_surf.fill((0, 0, 0, 0))
                    pygame.draw.circle(fov_surf, (*c, 80), (fov_r, fov_r), fov_r)
                    mag_bg.blit(fov_surf, (sp[0] - fov_r, sp[1] - fov_r))
                    
                    pygame.draw.circle(mag_bg, c, (int(sp[0]), int(sp[1])), 3)
                    pygame.draw.circle(mag_bg, (255, 255, 255), (int(sp[0]), int(sp[1])), 3, 1)

            # 描画
            bx = x + (self.panel_width - 28 - disp_size) // 2
            pygame.draw.rect(self.screen, COLOR_BAR_BORDER, pygame.Rect(bx-1, y-1, disp_size+2, disp_size+2), 1)
            self.screen.blit(mag_bg, (bx, y))
            
            y += disp_size + 10
        except Exception as e:
            err_text = self.font_small.render('Error rendering magnifier', True, COLOR_TEXT_DIM)
            self.screen.blit(err_text, (x + 10, y + 10))
            y += 30

        return y

    def _draw_section(self, x, y, title, items, key_value=False) :
        ts = self.font_title.render(title, True, COLOR_TEXT_ACCENT)
        self.screen.blit(ts, (x, y))
        y += 20
        for item in items :
            if key_value :
                key, val = item
                ks = self.font.render(f'{key}:', True, COLOR_TEXT_DIM)
                vs = self.font.render(val, True, COLOR_TEXT)
                self.screen.blit(ks, (x + 4, y))
                self.screen.blit(vs, (x + 85, y))
            else :
                s = self.font.render(str(item), True, COLOR_TEXT)
                self.screen.blit(s, (x + 4, y))
            y += 17
        return y + 4

    def _draw_divider(self, x, y, width) :
        pygame.draw.line(self.screen, COLOR_DIVIDER,
                         (x, y), (x + width, y), 1)
        return y + 8

    def _draw_sensor_bars(self, x, y, line_sensor_model, line_sensor_values) :
        ts = self.font_title.render('LINE SENSORS', True, COLOR_TEXT_ACCENT)
        self.screen.blit(ts, (x, y))
        y += 20

        if not line_sensor_values :
            return y

        bar_w = self.panel_width - 80
        bar_h = 14

        for i, val in enumerate(line_sensor_values) :
            label = self.font_small.render(f'S{i}', True, COLOR_TEXT_DIM)
            self.screen.blit(label, (x + 2, y))

            bx = x + 25
            bg_rect = pygame.Rect(bx, y, bar_w, bar_h)
            pygame.draw.rect(self.screen, COLOR_BAR_BG, bg_rect)

            fill_w = max(0, int(bar_w * val))
            if fill_w > 0 :
                fill_rect = pygame.Rect(bx, y, fill_w, bar_h)
                pygame.draw.rect(self.screen, sensor_color(val), fill_rect)

            pygame.draw.rect(self.screen, COLOR_BAR_BORDER, bg_rect, 1)

            val_text = self.font_small.render(f'{val:.2f}', True, COLOR_TEXT_DIM)
            self.screen.blit(val_text, (bx + bar_w + 4, y + 1))

            y += bar_h + 4

        y += 4
        offsets_str = ', '.join(f'{o:.1f}' for o in line_sensor_model._offsets)
        os_label = self.font_small.render(
            f'Offsets: [{offsets_str}]', True, COLOR_TEXT_DIM)
        self.screen.blit(os_label, (x + 2, y))
        y += 16

        return y
