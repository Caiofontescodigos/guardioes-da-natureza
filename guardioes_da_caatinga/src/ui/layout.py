import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.text import draw_text as _draw_text, draw_button_text

SAFE_MARGIN = 40
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

SERTAO_DARK = (25, 18, 10)
SERTAO_PANEL = (45, 32, 18)
SERTAO_BORDER = (139, 90, 43)
SERTAO_LIGHT = (180, 140, 60)
SERTAO_CREAM = (255, 240, 210)
SERTAO_GOLD = (255, 215, 0)
SERTAO_RED = (180, 60, 40)
SERTAO_GREEN = (80, 140, 60)

MOUSE_SCALE = 1.0
MOUSE_OFFSET = (0, 0)


def update_mouse_transform(scale, offset_x, offset_y):
    global MOUSE_SCALE, MOUSE_OFFSET
    MOUSE_SCALE = max(0.01, scale)
    MOUSE_OFFSET = (offset_x, offset_y)


def get_mouse_pos():
    x, y = pygame.mouse.get_pos()
    vx = (x - MOUSE_OFFSET[0]) / MOUSE_SCALE
    vy = (y - MOUSE_OFFSET[1]) / MOUSE_SCALE
    return (vx, vy)


class LayoutArea:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    @property
    def center_x(self):
        return self.x + self.w // 2

    @property
    def center_y(self):
        return self.y + self.h // 2

    def pad(self, top=0, bottom=0, left=0, right=0):
        return LayoutArea(
            self.x + left, self.y + top,
            self.w - left - right, self.h - top - bottom
        )

    def split_vertical(self, *ratios):
        total = sum(ratios)
        parts = []
        cur_y = self.y
        for r in ratios:
            h = int(self.h * r / total)
            parts.append(LayoutArea(self.x, cur_y, self.w, h))
            cur_y += h
        return parts

    def split_horizontal(self, *ratios):
        total = sum(ratios)
        parts = []
        cur_x = self.x
        for r in ratios:
            w = int(self.w * r / total)
            parts.append(LayoutArea(cur_x, self.y, w, self.h))
            cur_x += w
        return parts

    def center_rect(self, w, h):
        return pygame.Rect(
            self.x + (self.w - w) // 2,
            self.y + (self.h - h) // 2,
            w, h
        )

    def center_x_y(self):
        return (self.center_x, self.center_y)


class UILayout:
    def __init__(self, sw=SCREEN_WIDTH, sh=SCREEN_HEIGHT):
        self.sw = sw
        self.sh = sh
        self.safe = LayoutArea(SAFE_MARGIN, SAFE_MARGIN,
                               sw - SAFE_MARGIN * 2, sh - SAFE_MARGIN * 2)
        self.header = LayoutArea(0, 0, sw, 0)
        self.body = LayoutArea(0, 0, sw, 0)
        self.footer = LayoutArea(0, 0, sw, 0)
        self._compute()

    def _compute(self):
        header_h = 130
        footer_h = 50
        body_h = self.sh - header_h - footer_h

        self.header = LayoutArea(0, 0, self.sw, header_h)
        self.body = LayoutArea(0, header_h, self.sw, body_h)
        self.footer = LayoutArea(0, self.sh - footer_h, self.sw, footer_h)

    def make_button_row(self, count, btn_w, btn_h, spacing=12):
        total_w = count * btn_w + (count - 1) * spacing
        start_x = CENTER_X - total_w // 2
        btns = []
        for i in range(count):
            x = start_x + i * (btn_w + spacing)
            btns.append(pygame.Rect(x, 0, btn_w, btn_h))
        return btns

    def center_column(self, w, h, gap=0, count=1):
        total_h = count * h + max(0, count - 1) * gap
        start_y = self.body.center_y - total_h // 2
        rects = []
        for i in range(count):
            y = start_y + i * (h + gap)
            x = CENTER_X - w // 2
            rects.append(pygame.Rect(x, y, w, h))
        return rects


def draw_sertao_panel(surface, x, y, w, h, border_color=SERTAO_BORDER, alpha=220):
    shadow = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 100), (0, 0, w + 6, h + 6), border_radius=10)
    surface.blit(shadow, (x + 3, y + 3))

    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*SERTAO_PANEL, alpha), (0, 0, w, h), border_radius=10)
    surface.blit(panel, (x, y))

    pygame.draw.rect(surface, border_color, (x, y, w, h), 2, border_radius=10)


def draw_sertao_button(surface, rect, text, is_hovered=False, enabled=True, color=None,
                       font_size=24):
    if color is None:
        color = SERTAO_PANEL

    if not enabled:
        bg = (40, 30, 20)
        border = (80, 60, 40)
        text_color = (120, 100, 80)
    elif is_hovered:
        bg = tuple(min(255, c + 35) for c in color)
        border = SERTAO_GOLD
        text_color = SERTAO_GOLD
    else:
        bg = color
        border = SERTAO_BORDER
        text_color = SERTAO_CREAM

    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)

    draw_button_text(surface, text, rect, color=text_color, font_size=font_size)


def draw_text(surface, text, pos, font_size=24, color=(255, 255, 255), center=False):
    return _draw_text(surface, text, pos, font_size=font_size, color=color,
                      center=center)
