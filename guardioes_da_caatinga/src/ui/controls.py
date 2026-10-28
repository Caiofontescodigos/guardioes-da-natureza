"""Reusable controls used by the settings screen.

Every control is a self contained widget that knows how to draw itself and
how to translate mouse events into a generic action tuple. The settings
screen only needs to lay the controls out and forward the returned actions
to ``Game``.

Returned actions:

    ("setting", key, value, commit)  -> change a setting
    ("action", name)                 -> run a screen action
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.layout import (SERTAO_PANEL, SERTAO_BORDER, SERTAO_GOLD,
                           SERTAO_CREAM, SERTAO_GREEN,
                           draw_sertao_button, get_mouse_pos)
from src.ui.text import wrap_text, draw_button_text, draw_text

HOVER_BG = (62, 46, 26)
DISABLED_TEXT = (120, 100, 80)
LABEL_SIZE = 20
OPTION_SIZE = 17


def _label(surface, rect, text, enabled=True, size=LABEL_SIZE):
    color = SERTAO_CREAM if enabled else DISABLED_TEXT
    return draw_text(surface, text, (rect.x, rect.y + size // 2 + 4),
                     font_size=size, color=color)


class ToggleControl:
    """A labelled on/off switch. The whole row is clickable."""

    def __init__(self, key, label, value, rect, enabled=True):
        self.key = key
        self.label = label
        self.value = bool(value)
        self.rect = pygame.Rect(rect)
        self.enabled = enabled

    @property
    def pill_rect(self):
        width, height = 58, 30
        return pygame.Rect(self.rect.right - width, self.rect.centery - height // 2,
                           width, height)

    def draw(self, surface):
        hovered = self.enabled and self.rect.collidepoint(get_mouse_pos())
        if hovered:
            bg = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            bg.fill((*HOVER_BG, 120))
            surface.blit(bg, self.rect.topleft)

        _label(surface, self.rect, self.label, self.enabled)

        pill = self.pill_rect
        if not self.enabled:
            track = (55, 45, 35)
        else:
            track = SERTAO_GREEN if self.value else (85, 68, 48)
        pygame.draw.rect(surface, track, pill, border_radius=pill.h // 2)
        pygame.draw.rect(surface, SERTAO_BORDER, pill, 2, border_radius=pill.h // 2)

        radius = pill.h // 2 - 4
        knob_x = pill.right - radius - 4 if self.value else pill.x + radius + 4
        knob_color = SERTAO_CREAM if self.enabled else DISABLED_TEXT
        pygame.draw.circle(surface, knob_color, (knob_x, pill.centery), radius)

    def handle_event(self, event):
        if not self.enabled:
            return None
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos)):
            self.value = not self.value
            return ("setting", self.key, self.value, True)
        return None


class SegmentedControl:
    """A labelled row of mutually exclusive options."""

    def __init__(self, key, label, options, value, rect, enabled=True):
        self.key = key
        self.label = label
        self.options = list(options)  # [(label, value), ...]
        self.value = value
        self.rect = pygame.Rect(rect)
        self.enabled = enabled
        self.option_rects = self._build_option_rects()

    def _build_option_rects(self):
        gap = 6
        top = self.rect.y + 30
        height = 34
        count = max(1, len(self.options))
        width = (self.rect.w - gap * (count - 1)) // count
        rects = []
        for i in range(count):
            rects.append(pygame.Rect(self.rect.x + i * (width + gap), top,
                                     width, height))
        return rects

    def draw(self, surface):
        _label(surface, self.rect, self.label, self.enabled)
        mouse = get_mouse_pos()
        for (text, value), rect in zip(self.options, self.option_rects):
            selected = value == self.value
            hovered = self.enabled and rect.collidepoint(mouse)
            if not self.enabled:
                bg, border, text_color = (45, 36, 26), (80, 60, 40), DISABLED_TEXT
            elif selected:
                bg, border, text_color = SERTAO_GREEN, SERTAO_GOLD, SERTAO_CREAM
            elif hovered:
                bg, border, text_color = (72, 54, 30), SERTAO_GOLD, SERTAO_GOLD
            else:
                bg, border, text_color = SERTAO_PANEL, SERTAO_BORDER, SERTAO_CREAM
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, border, rect, 2, border_radius=6)
            draw_button_text(surface, text, rect, color=text_color,
                             font_size=OPTION_SIZE, min_font=12, max_lines=1)

    def handle_event(self, event):
        if not self.enabled:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for (_text, value), rect in zip(self.options, self.option_rects):
                if rect.collidepoint(event.pos):
                    if value == self.value:
                        return None
                    self.value = value
                    return ("setting", self.key, value, True)
        return None


class SliderControl:
    """A labelled horizontal slider with 10% steps.

    While dragging the value is previewed (``commit=False``); the final value
    is committed when the mouse button is released.
    """

    STEP = 10

    def __init__(self, key, label, value, rect, enabled=True):
        self.key = key
        self.label = label
        self.value = self._clamp(value)
        self.rect = pygame.Rect(rect)
        self.enabled = enabled
        self.dragging = False
        self.track_rect = pygame.Rect(self.rect.x, self.rect.y + 40,
                                      self.rect.w, 10)
        self.hit_rect = pygame.Rect(self.rect.x - 10, self.rect.y + 26,
                                    self.rect.w + 20, 40)

    def _clamp(self, value):
        return max(0.0, min(1.0, round(float(value), 2)))

    def _value_from_pos(self, x):
        ratio = (x - self.track_rect.x) / max(1, self.track_rect.w)
        ratio = max(0.0, min(1.0, ratio))
        return round(ratio * self.STEP) / self.STEP

    def draw(self, surface):
        _label(surface, self.rect, self.label, self.enabled)
        text = f"{int(round(self.value * 100))}%"
        draw_text(surface, text, (self.rect.right, self.rect.y + 14),
                  font_size=18, color=SERTAO_GOLD if self.enabled else DISABLED_TEXT,
                  align="right")

        track = self.track_rect
        pygame.draw.rect(surface, (70, 56, 38), track, border_radius=track.h // 2)
        filled = pygame.Rect(track.x, track.y,
                             int(track.w * self.value), track.h)
        if filled.w > 0:
            color = SERTAO_GOLD if self.enabled else (110, 90, 60)
            pygame.draw.rect(surface, color, filled, border_radius=track.h // 2)

        knob_x = track.x + int(track.w * self.value)
        knob_color = SERTAO_CREAM if self.enabled else DISABLED_TEXT
        pygame.draw.circle(surface, knob_color, (knob_x, track.centery), 9)
        pygame.draw.circle(surface, SERTAO_BORDER, (knob_x, track.centery), 9, 2)

    def handle_event(self, event):
        if not self.enabled:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hit_rect.collidepoint(event.pos):
                self.dragging = True
                self.value = self._value_from_pos(event.pos[0])
                return ("setting", self.key, self.value, False)
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.value = self._value_from_pos(event.pos[0])
            return ("setting", self.key, self.value, False)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                self.value = self._value_from_pos(event.pos[0])
                return ("setting", self.key, self.value, True)
        return None


class ActionButton:
    """A regular action button (reset defaults, back, ...)."""

    def __init__(self, action, label, rect, color=None, font_size=22,
                 enabled=True):
        self.action = action
        self.label = label
        self.rect = pygame.Rect(rect)
        self.color = color
        self.font_size = font_size
        self.enabled = enabled

    def draw(self, surface):
        hovered = self.enabled and self.rect.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.rect, self.label, is_hovered=hovered,
                           enabled=self.enabled,
                           color=self.color, font_size=self.font_size)

    def handle_event(self, event):
        if not self.enabled:
            return None
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos)):
            return ("action", self.action)
        return None


class ConfirmDialog:
    """Modal confirmation box shared by reset-defaults and quit flows."""

    def __init__(self, title="", message="", confirm_label="SIM",
                 cancel_label="CANCELAR", confirm_color=SERTAO_GREEN):
        self.title = title
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_color = confirm_color
        self.action = None
        self.visible = False

        self.panel = pygame.Rect((SCREEN_WIDTH - 640) // 2,
                                 (SCREEN_HEIGHT - 280) // 2, 640, 280)
        self.confirm_button = pygame.Rect(0, 0, 200, 50)
        self.cancel_button = pygame.Rect(0, 0, 200, 50)
        self._build_rects()

    def _build_rects(self):
        button_w, button_h = 200, 50
        gap = 24
        total = button_w * 2 + gap
        start_x = self.panel.centerx - total // 2
        y = self.panel.bottom - 76
        self.cancel_button = pygame.Rect(start_x, y, button_w, button_h)
        self.confirm_button = pygame.Rect(start_x + button_w + gap, y,
                                          button_w, button_h)

    def open(self, title=None, message=None, confirm_label=None, action=None):
        if title is not None:
            self.title = title
        if message is not None:
            self.message = message
        if confirm_label is not None:
            self.confirm_label = confirm_label
        self.action = action
        self.visible = True

    def close(self):
        self.visible = False
        self.action = None

    def handle_event(self, event):
        if not self.visible:
            return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return "cancel"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.confirm_button.collidepoint(event.pos):
                return "confirm"
            if self.cancel_button.collidepoint(event.pos):
                return "cancel"
        return None

    def draw(self, surface):
        if not self.visible:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, SERTAO_PANEL, self.panel, border_radius=12)
        pygame.draw.rect(surface, SERTAO_GOLD, self.panel, 2, border_radius=12)

        draw_text(surface, self.title,
                  (self.panel.centerx, self.panel.y + 40),
                  font_size=30, color=SERTAO_GOLD, center=True)

        lines = wrap_text(self.message, 20, self.panel.w - 80)
        y = self.panel.y + 78
        for line in lines[:4]:
            draw_text(surface, line, (self.panel.centerx, y),
                      font_size=20, color=SERTAO_CREAM, center=True)
            y += 26

        hover = get_mouse_pos()
        draw_sertao_button(surface, self.cancel_button, self.cancel_label,
                           is_hovered=self.cancel_button.collidepoint(hover),
                           color=(90, 70, 50), font_size=20)
        draw_sertao_button(surface, self.confirm_button, self.confirm_label,
                           is_hovered=self.confirm_button.collidepoint(hover),
                           color=self.confirm_color, font_size=20)
