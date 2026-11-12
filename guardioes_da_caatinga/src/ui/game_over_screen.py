"""Tela de Game Over baseada na arte original ``TelaGameOver.png``.

A arte fornecida já contém o título, os rótulos das estatísticas e o botão
"Tentar Novamente"; esta tela apenas desenha os valores, as miniaturas da
equipe e áreas clicáveis sobre os elementos existentes. A arte é exibida como
um painel compacto sobre o fundo da região em que a equipe foi derrotada.
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.layout import draw_sertao_button, SERTAO_GOLD, SERTAO_CREAM
from src.ui.text import draw_text_centered, draw_text_centered_in_rect


class GameOverScreen:
    """Interactive overlay for the supplied Game Over artwork."""

    # Native size of ``TelaGameOver.png`` (used for clickable coordinates).
    SOURCE_WIDTH = 1600
    SOURCE_HEIGHT = 900
    ARTWORK_FILENAME = "TelaGameOver.png"

    # The artwork is shown as a panel over the region where the run ended
    # instead of covering the whole screen.
    PANEL_WIDTH_RATIO = 0.75
    PANEL_HEIGHT_RATIO = 0.82

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

    def __init__(self, assets, save_data=None, party=None,
                 biome_id=None, boss_phase=False):
        self.assets = assets
        self.save_data = save_data or {}
        self.party = list(party or [])
        self.biome_id = biome_id or "caatinga"
        self.boss_phase = bool(boss_phase)
        self.hover = None
        self._menu_font = max(14, int(20 * self._scale()))

    # -------------------------------------------------------------- layout
    def _image_rect(self):
        """Area occupied by the artwork, fitted without distortion."""
        max_width = max(1, int(SCREEN_WIDTH * self.PANEL_WIDTH_RATIO))
        max_height = max(1, int(SCREEN_HEIGHT * self.PANEL_HEIGHT_RATIO))
        ratio = min(max_width / self.SOURCE_WIDTH,
                    max_height / self.SOURCE_HEIGHT)
        width = max(1, int(self.SOURCE_WIDTH * ratio))
        height = max(1, int(self.SOURCE_HEIGHT * ratio))
        return pygame.Rect((SCREEN_WIDTH - width) // 2,
                           (SCREEN_HEIGHT - height) // 2,
                           width, height)

    def _scale(self):
        return self._image_rect().width / self.SOURCE_WIDTH

    def _scale_x(self):
        return self._image_rect().width / self.SOURCE_WIDTH

    def _scale_y(self):
        return self._image_rect().height / self.SOURCE_HEIGHT

    def _rect(self, source_rect):
        left, top, width, height = source_rect
        base = self._image_rect()
        sx, sy = self._scale_x(), self._scale_y()
        return pygame.Rect(base.x + int(left * sx), base.y + int(top * sy),
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

    def _draw_region_background(self, surface):
        """Fill the canvas with the region where the party was defeated."""
        surface.fill((24, 14, 8))
        if self.assets is None:
            return
        background = self.assets.get_map_background(
            self.biome_id, self.boss_phase,
            surface.get_width(), surface.get_height())
        if background is not None:
            surface.blit(background, (0, 0))
        else:
            self.assets.draw_background(surface, "map")

        # Darken the region art so the Game Over panel stands out.
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((10, 7, 4, 145))
        surface.blit(shade, (0, 0))

    def draw(self, surface):
        self._draw_region_background(surface)

        background = None
        if self.assets is not None:
            # Fit the original artwork inside the canvas, preserving its
            # 16:9 proportions instead of stretching it.
            base = self._image_rect()
            background = self.assets.get_fitted_image(
                self.ARTWORK_FILENAME, base.w, base.h)
        if background is not None:
            base = background.get_rect(center=(SCREEN_WIDTH // 2,
                                               SCREEN_HEIGHT // 2))
            shadow = pygame.Surface((base.w + 28, base.h + 28),
                                    pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(),
                             border_radius=18)
            surface.blit(shadow, (base.x - 14, base.y - 14))
            surface.blit(background, base)

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
        label_h = max(18, int(28 * self._scale_y()))
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

            # Keep the name/level readable over the supplied frame without
            # covering the portrait with a large panel.
            label_rect = pygame.Rect(
                target.x + int(target.w * 0.08),
                target.bottom - label_h,
                target.w - int(target.w * 0.16),
                label_h)
            strip = pygame.Surface(label_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(strip, (22, 14, 8, 185), strip.get_rect(),
                             border_radius=max(4, label_h // 3))
            surface.blit(strip, label_rect.topleft)

            label = f"{animal.name}  Lv.{animal.level}"
            draw_text_centered_in_rect(
                surface, label, label_rect,
                max(12, int(18 * self._scale_y())), SERTAO_CREAM,
                min_font=10)

    def _draw_menu_button(self, surface):
        draw_sertao_button(
            surface, self.menu_rect, "VOLTAR AO MENU",
            is_hovered=self.hover == "menu",
            font_size=self._menu_font)