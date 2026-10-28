from dataclasses import dataclass

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


@dataclass(frozen=True)
class ButtonMetrics:
    """Medidas responsivas de um tipo de botao."""
    width: int
    height: int
    font_size: int
    gap: int = 0


# Cada preset guarda (proporcao, minimo, maximo). As proporcoes sao aplicadas
# sobre o canvas virtual e os limites evitam botoes ilegiveis ou gigantes.
_BUTTON_PRESETS = {
    "menu": {
        "width": (0.300, 360, 460),
        "height": (0.086, 56, 72),
        "font": (0.039, 24, 32),
        "gap": (0.018, 10, 18),
    },
    "nav": {
        "width": (0.130, 150, 200),
        "height": (0.072, 46, 58),
        "font": (0.033, 22, 28),
        "gap": (0.0, 0, 0),
    },
    "tab": {
        "width": (0.203, 220, 300),
        "height": (0.064, 40, 54),
        "font": (0.031, 20, 26),
        "gap": (0.017, 8, 16),
    },
    "toggle": {
        "width": (0.280, 320, 420),
        "height": (0.086, 56, 72),
        "font": (0.036, 24, 30),
        "gap": (0.0, 0, 0),
    },
}


def ui_scale():
    """Fator de escala do canvas virtual em relacao ao projeto base 1280x720."""
    return min(SCREEN_WIDTH / 1280.0, SCREEN_HEIGHT / 720.0)


def get_button_metrics(kind="menu"):
    """Retorna as medidas proporcionais de um tipo de botao."""
    spec = _BUTTON_PRESETS.get(kind, _BUTTON_PRESETS["menu"])
    scale = ui_scale()

    def _dim(key, base):
        ratio, low, high = spec[key]
        return int(round(max(low, min(high, base * ratio * scale))))

    return ButtonMetrics(
        width=_dim("width", SCREEN_WIDTH),
        height=_dim("height", SCREEN_HEIGHT),
        font_size=_dim("font", SCREEN_HEIGHT),
        gap=_dim("gap", SCREEN_HEIGHT),
    )


def make_centered_column(count, metrics=None, center_y=None, offset_y=0):
    """Cria uma coluna centralizada de ``count`` botoes."""
    m = metrics or get_button_metrics()
    total_h = count * m.height + max(0, count - 1) * m.gap
    start_y = (center_y if center_y is not None else CENTER_Y) - total_h // 2 + offset_y
    x = CENTER_X - m.width // 2
    return [
        pygame.Rect(x, start_y + i * (m.height + m.gap), m.width, m.height)
        for i in range(count)
    ]


def make_centered_tabs(count, metrics=None, y=0):
    """Cria uma linha centralizada de abas."""
    m = metrics or get_button_metrics("tab")
    total_w = count * m.width + max(0, count - 1) * m.gap
    start_x = CENTER_X - total_w // 2
    return [
        pygame.Rect(start_x + i * (m.width + m.gap), y, m.width, m.height)
        for i in range(count)
    ]


def make_back_button(metrics=None, margin=18, x=SAFE_MARGIN):
    """Cria o botao Voltar no canto inferior esquerdo, com margem segura."""
    m = metrics or get_button_metrics("nav")
    return pygame.Rect(x, SCREEN_HEIGHT - margin - m.height, m.width, m.height)


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
