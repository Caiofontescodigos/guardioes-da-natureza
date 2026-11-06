"""Tela de Game Over baseada na arte original ``TelaGameOver.jpeg``.

A arte fornecida já contém o título, os rótulos das estatísticas e o botão
"Tentar Novamente"; esta tela apenas desenha os valores, as miniaturas da
equipe e áreas clicáveis sobre os elementos existentes.
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.layout import draw_sertao_button, SERTAO_GOLD, SERTAO_CREAM
from src.ui.text import draw_text_centered


class GameOverScreen:
    """Interactive overlay for the supplied Game Over artwork."""

    # Native size of ``TelaGameOver.jpeg`` (used for clickable coordinates).
    SOURCE_WIDTH = 1600
    SOURCE_HEIGHT = 900

    # Areas drawn in the original image (left, top, width, height).
    _STAT_BOXES = (
        (285, 383, 226, 61),
        (672, 383, 238, 61),
        (1063, 383, 233, 61),
    )
    _PORTRAIT_FRAMES = (
        (355, 495, 275, 217),
        (683, 495, 275, 217),
        (1012, 495, 275, 217),
    )
    _RETRY_BUTTON = (515, 753, 575, 95)
    # The artwork has no menu button; this compact secondary action is drawn
    # over the decorative foliage in the lower-left corner.
    _MENU_BUTTON = (50, 790, 250, 58)

    def __init__(self, assets, save_data=None, party=None):
        self.assets = assets
        self.save_data = save_data or {}
        self.party = list(party or [])
        self.hover = None
        self._menu_font = max(14, int(20 * self._scale_y()))

    # -------------------------------------------------------------- layout
    def _scale_x(self):
        return SCREEN_WIDTH / self.SOURCE_WIDTH

    def _scale_y(self):
        return SCREEN_HEIGHT / self.SOURCE_HEIGHT

    def _rect(self, source_rect):
        left, top, width, height = source_rect
        sx, sy = self._scale_x(), self._scale_y()
        return pygame.Rect(int(left * sx), int(top * sy),
                           max(1, int(width * sx)), max(1, int(height * sy)))

    @property
    def retry_rect(self):
        return self._rect(self._RETRY_BUTTON)

    @property
    def menu_rect(self):
        return self._rect(self._MENU_BUTTON)

    # --------------------------------------------------------------- input
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = None
            if self.retry_rect.collidepoint(event.pos):
                self.hover = "retry"
            elif self.menu_rect.collidepoint(event.pos):
                self.hover = "menu"
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                             pygame.K_SPACE):
                return "retry"
            if event.key == pygame.K_ESCAPE:
                return "menu"
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.retry_rect.collidepoint(event.pos):
                return "retry"
            if self.menu_rect.collidepoint(event.pos):
                return "menu"
        return None

    # --------------------------------------------------------------- draw
    def _stat_value(self, key):
        stats = self.save_data.get("statistics", {}) or {}
        return str(stats.get(key, 0))

    def draw(self, surface):
        background = None
        if self.assets is not None:
            background = self.assets.get_background(
                "game_over", surface.get_width(), surface.get_height())
        if background is not None:
            surface.blit(background, (0, 0))
        else:
            surface.fill((24, 14, 8))

        self._draw_stats(surface)
        self._draw_party(surface)
        self._draw_menu_button(surface)

    def _draw_stats(self, surface):
        values = (
            self._stat_value("enemies_defeated"),
            self._stat_value("bosses_defeated"),
            self._stat_value("gold_earned"),
        )
        font_size = max(16, int(34 * self._scale_y()))
        for rect, value in zip(self._STAT_BOXES, values):
            target = self._rect(rect)
            draw_text_centered(surface, value, target.centerx,
                               target.centery, font_size, SERTAO_GOLD)

    def _draw_party(self, surface):
        if self.assets is None:
            return
        for frame, animal in zip(self._PORTRAIT_FRAMES, self.party[:3]):
            target = self._rect(frame)
            inner = target.inflate(-int(target.w * 0.14),
                                    -int(target.h * 0.14))
            stage = getattr(animal, "evolution_stage", 0) or 0
            sprite = self.assets.get_animal_sprite(
                animal.animal_id, evolution_stage=stage,
                max_width=max(1, inner.w), max_height=max(1, inner.h))
            if sprite is not None:
                surface.blit(sprite, sprite.get_rect(center=inner.center))

            label = f"{animal.name}  Lv.{animal.level}"
            draw_text_centered(
                surface, label, target.centerx,
                target.bottom - int(target.h * 0.08),
                max(12, int(18 * self._scale_y())), SERTAO_CREAM)

    def _draw_menu_button(self, surface):
        draw_sertao_button(
            surface, self.menu_rect, "VOLTAR AO MENU",
            is_hovered=self.hover == "menu",
            font_size=self._menu_font)
