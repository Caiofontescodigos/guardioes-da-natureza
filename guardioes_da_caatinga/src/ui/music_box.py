"""Music box screen.

The screen is only a view/controller for the single :class:`MusicManager`.
It can preview any allowed track, pause/resume, stop and change the music
volume.  When the player leaves, ``Game`` restores the contextual track for
the current game state, so a manual preview never overrides a battle or boss
track permanently.
"""

import os

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.controls import SliderControl
from src.ui.layout import (SAFE_MARGIN, CENTER_X, SERTAO_BORDER,
                           SERTAO_CREAM, SERTAO_GOLD, SERTAO_GREEN,
                           SERTAO_PANEL, SERTAO_LIGHT,
                           draw_sertao_panel, draw_sertao_button, draw_text,
                           get_mouse_pos)
from src.ui.text import draw_text_centered, draw_text_right


def _same_track(left, right):
    from src.audio.music_manager import _track_key
    return bool(left) and bool(right) and _track_key(left) == _track_key(right)


class MusicBoxScreen:
    """Manual music player integrated with the contextual audio system."""

    ROW_HEIGHT = 56
    ROW_GAP = 8

    def __init__(self, music_manager, assets=None, settings=None):
        self.music_manager = music_manager
        self.assets = assets
        self.settings = settings or {}
        self.tracks = music_manager.available_tracks()
        self.hovered_track = -1
        self.hovered_action = None

        self.panel = pygame.Rect(SAFE_MARGIN, 104,
                                 SCREEN_WIDTH - SAFE_MARGIN * 2, 552)
        self.list_rect = pygame.Rect(self.panel.x + 22, self.panel.y + 74,
                                     690, 340)
        self.info_rect = pygame.Rect(self.list_rect.right + 18,
                                     self.list_rect.y, 250,
                                     self.list_rect.h)
        self.track_rects = []
        self._build_track_rects()

        control_y = self.panel.bottom - 72
        self.play_button = pygame.Rect(self.panel.x + 24, control_y, 190, 46)
        self.stop_button = pygame.Rect(self.panel.x + 230, control_y, 160, 46)
        self.back_button = pygame.Rect(self.panel.x + 406, control_y, 160, 46)

        self.volume_slider = SliderControl(
            "music_volume", "Volume da musica",
            float(self.settings.get("music_volume", 0.7)),
            pygame.Rect(self.panel.right - 310, control_y - 34, 280, 72))

    def _build_track_rects(self):
        self.tracks = self.music_manager.available_tracks()
        self.track_rects = []
        y = self.list_rect.y
        for _track in self.tracks:
            self.track_rects.append(
                pygame.Rect(self.list_rect.x, y, self.list_rect.w,
                            self.ROW_HEIGHT))
            y += self.ROW_HEIGHT + self.ROW_GAP

    def sync(self, settings):
        self.settings = settings or {}
        self.volume_slider.value = float(
            self.settings.get("music_volume", 0.7))
        self._build_track_rects()

    # ------------------------------------------------------------- events

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered_track = -1
            self.hovered_action = None
            for index, rect in enumerate(self.track_rects):
                if rect.collidepoint(event.pos):
                    self.hovered_track = index
                    break
            for name, rect in (("play", self.play_button),
                               ("stop", self.stop_button),
                               ("back", self.back_button)):
                if rect.collidepoint(event.pos):
                    self.hovered_action = name
                    break

        volume_result = self.volume_slider.handle_event(event)
        if volume_result:
            _kind, _key, value, commit = volume_result
            return ("volume", value, commit)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.track_rects):
                if rect.collidepoint(event.pos):
                    track = self.tracks[index]
                    return ("play", track["filename"])

            if self.play_button.collidepoint(event.pos):
                return ("toggle_pause",)
            if self.stop_button.collidepoint(event.pos):
                return ("stop",)
            if self.back_button.collidepoint(event.pos):
                return "back"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        return None

    # --------------------------------------------------------------- draw

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "settings")
        else:
            surface.fill((25, 18, 10))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        surface.blit(overlay, (0, 0))

        draw_text_centered(surface, "CAIXA DE MUSICA", CENTER_X, 48,
                           42, SERTAO_GOLD)
        draw_text_centered(
            surface, "Escolha uma faixa para ouvir. A selecao manual nao "
                     "substitui as musicas de batalha ou de chefe.",
            CENTER_X, 82, 17, SERTAO_LIGHT)

        draw_sertao_panel(surface, self.panel.x, self.panel.y,
                          self.panel.w, self.panel.h)
        draw_text(surface, "FAIXAS DISPONIVEIS", (self.list_rect.x,
                                                  self.list_rect.y - 24),
                  font_size=22, color=SERTAO_GOLD)
        draw_text(surface, "REPRODUCAO", (self.info_rect.centerx,
                                          self.info_rect.y - 24),
                  font_size=22, color=SERTAO_GOLD, center=True)

        if not self.tracks:
            draw_text(surface, "Nenhuma faixa de musica encontrada.",
                      (self.list_rect.x, self.list_rect.centery),
                      font_size=20, color=SERTAO_CREAM)
        else:
            for index, (track, rect) in enumerate(
                    zip(self.tracks, self.track_rects)):
                self._draw_track_row(surface, track, rect, index)

        self._draw_info_panel(surface)
        self._draw_controls(surface)

    def _draw_track_row(self, surface, track, rect, index):
        current = _same_track(track["filename"],
                              self.music_manager.current_track)
        hovered = self.hovered_track == index
        border = SERTAO_GOLD if current else SERTAO_BORDER
        fill = (72, 55, 30) if hovered else ((55, 48, 28) if current
                                             else SERTAO_PANEL)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, 2, border_radius=8)

        draw_text(surface, track["title"], (rect.x + 16, rect.centery - 9),
                  font_size=20, color=SERTAO_GOLD if current else SERTAO_CREAM)
        draw_text(surface, track["category"], (rect.x + 16, rect.centery + 13),
                  font_size=14, color=SERTAO_LIGHT)

        status = "TOCANDO" if current else "OUVIR"
        status_color = SERTAO_GREEN if current else SERTAO_LIGHT
        draw_text_right(surface, status, (rect.right - 16, rect.centery),
                        font_size=15, color=status_color)

    def _draw_info_panel(self, surface):
        rect = self.info_rect
        pygame.draw.rect(surface, (38, 28, 16), rect, border_radius=8)
        pygame.draw.rect(surface, SERTAO_BORDER, rect, 2, border_radius=8)

        current = self.music_manager.current_track
        title = (self.music_manager.track_label(current)
                 if current else "Nenhuma musica")
        state = "Pausada" if self.music_manager.paused else "Tocando"
        if not current:
            state = "Parada"

        draw_text_centered(surface, "AGORA", rect.centerx, rect.y + 26,
                           17, SERTAO_LIGHT)
        draw_text_centered(surface, title, rect.centerx, rect.y + 66,
                           20, SERTAO_GOLD)
        draw_text_centered(surface, state, rect.centerx, rect.y + 98,
                           18, SERTAO_GREEN if state == "Tocando"
                           else SERTAO_CREAM)
        draw_text_centered(surface, "Contexto", rect.centerx, rect.y + 148,
                           15, SERTAO_LIGHT)
        draw_text_centered(surface, self.music_manager.context_label(),
                           rect.centerx, rect.y + 174, 17, SERTAO_CREAM)

        if self.music_manager.muted:
            draw_text_centered(surface, "MUDO ATIVO", rect.centerx,
                               rect.y + 218, 16, (220, 130, 80))

    def _draw_controls(self, surface):
        paused = self.music_manager.paused
        play_label = "RETOMAR" if paused else "PAUSAR"
        draw_sertao_button(surface, self.play_button, play_label,
                           is_hovered=self.hovered_action == "play",
                           enabled=bool(self.music_manager.current_track))
        draw_sertao_button(surface, self.stop_button, "PARAR",
                           is_hovered=self.hovered_action == "stop",
                           enabled=bool(self.music_manager.current_track))
        draw_sertao_button(surface, self.back_button, "VOLTAR",
                           is_hovered=self.hovered_action == "back")

        self.volume_slider.draw(surface)
        draw_text(surface, "As configuracoes de volume e mudo sao as mesmas "
                           "do jogo.",
                  (self.panel.x + 24, self.panel.bottom - 14),
                  font_size=14, color=SERTAO_LIGHT)
