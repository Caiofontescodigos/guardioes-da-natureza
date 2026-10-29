"""Animated achievement unlock toasts."""

import time

import pygame

from config import SCREEN_WIDTH
from src.ui.layout import draw_sertao_panel, SERTAO_GOLD, SERTAO_CREAM
from src.ui.text import draw_text
from src.ui.achievements_screen import draw_medal, TIER_COLORS

TOAST_W = 380
TOAST_H = 84
TOAST_MARGIN = 18
TOAST_DURATION = 3.6
SLIDE_TIME = 0.22


class AchievementToast:
    def __init__(self, entry, started_at=None):
        self.entry = entry
        self.started_at = started_at if started_at is not None else time.time()

    def elapsed(self):
        return time.time() - self.started_at

    def is_done(self):
        return self.elapsed() >= TOAST_DURATION

    def _x_position(self):
        elapsed = self.elapsed()
        target_x = SCREEN_WIDTH - TOAST_W - TOAST_MARGIN
        if elapsed < SLIDE_TIME:
            progress = elapsed / SLIDE_TIME
        elif elapsed > TOAST_DURATION - SLIDE_TIME:
            progress = max(0.0, (TOAST_DURATION - elapsed) / SLIDE_TIME)
        else:
            progress = 1.0
        # Smooth ease-out.
        progress = 1 - (1 - progress) ** 3
        return int(target_x + (TOAST_W + TOAST_MARGIN) * (1 - progress))

    def draw(self, surface):
        entry = self.entry
        x = self._x_position()
        y = TOAST_MARGIN
        rect = pygame.Rect(x, y, TOAST_W, TOAST_H)
        tier_color = TIER_COLORS.get(entry.get("tier"), SERTAO_GOLD)
        draw_sertao_panel(surface, rect.x, rect.y, rect.w, rect.h,
                          border_color=SERTAO_GOLD, alpha=238)

        medal_rect = pygame.Rect(rect.x + 14, rect.y + 14, 54, 54)
        draw_medal(surface, medal_rect, entry.get("category", "extras"),
                   entry.get("tier", "bronze"), True)

        draw_text(surface, "CONQUISTA DESBLOQUEADA",
                  (rect.x + 80, rect.y + 12), font_size=13,
                  color=tier_color)
        name = entry.get("name", "")
        if len(name) > 26:
            name = name[:25] + "..."
        draw_text(surface, name, (rect.x + 80, rect.y + 30),
                  font_size=20, color=SERTAO_GOLD)
        points = entry.get("points", 0)
        draw_text(surface, f"+{points} pts", (rect.right - 14,
                                              rect.bottom - 22),
                  font_size=14, color=SERTAO_CREAM, align="right")


class ToastManager:
    """Shows one toast at a time and queues the rest."""

    def __init__(self, on_show=None):
        self.queue = []
        self.current = None
        self.on_show = on_show

    def push(self, entries):
        if not entries:
            return
        self.queue.extend(entries)

    def update(self):
        if self.current is not None and not self.current.is_done():
            return
        if self.current is not None:
            self.current = None
        if not self.queue:
            return
        self.current = AchievementToast(self.queue.pop(0))
        if self.on_show:
            self.on_show(self.current.entry)

    def draw(self, surface):
        if self.current is not None:
            self.current.draw(surface)

    def clear(self):
        self.queue = []
        self.current = None
