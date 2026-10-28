"""Settings screen with TELA / AUDIO / JOGO / DADOS sections."""

import pygame

from config import SCREEN_WIDTH, DEFAULT_GLOBAL_SETTINGS
from src.ui.layout import (UILayout, SAFE_MARGIN, CENTER_X,
                           SERTAO_BORDER, SERTAO_GOLD,
                           SERTAO_LIGHT, draw_sertao_panel, draw_text)
from src.ui.controls import (ToggleControl, SegmentedControl, SliderControl,
                             ActionButton, ConfirmDialog)

RESOLUTIONS = [
    ("1280x720", [1280, 720]),
    ("1600x900", [1600, 900]),
    ("1920x1080", [1920, 1080]),
]

SPEEDS = [
    ("1x", 1),
    ("2x", 2),
    ("3x", 3),
]

PANEL_Y = 118
PANEL_H = 430
COLUMN_GAP = 20


class SettingsScreen:
    """Configuracoes gerais: tela, audio, jogo e dados."""

    def __init__(self, assets=None, settings=None):
        self.assets = assets
        self.layout = UILayout()
        self.dialog = ConfirmDialog(
            title="Restaurar padroes",
            message="Todas as configuracoes voltarao ao padrao de fabrica. "
                    "Seus saves e progresso nao serao apagados.",
            confirm_label="RESTAURAR",
            cancel_label="CANCELAR",
            confirm_color=(150, 80, 40),
        )
        self._build()
        self.sync(settings or DEFAULT_GLOBAL_SETTINGS)

    # ------------------------------------------------------------ layout

    def _build(self):
        total_w = SCREEN_WIDTH - SAFE_MARGIN * 2
        col_w = (total_w - COLUMN_GAP * 2) // 3
        self.columns = [
            ("TELA", pygame.Rect(SAFE_MARGIN, PANEL_Y, col_w, PANEL_H)),
            ("AUDIO", pygame.Rect(SAFE_MARGIN + col_w + COLUMN_GAP, PANEL_Y,
                                  col_w, PANEL_H)),
            ("JOGO", pygame.Rect(SAFE_MARGIN + 2 * (col_w + COLUMN_GAP), PANEL_Y,
                                 col_w, PANEL_H)),
        ]

        row_x = self.columns[0][1].x + 18
        row_w = col_w - 36
        row_y = PANEL_Y + 54

        self.fullscreen_toggle = ToggleControl(
            "fullscreen", "Tela cheia", False,
            pygame.Rect(row_x, row_y, row_w, 46))
        self.resolution_seg = SegmentedControl(
            "window_size", "Resolucao", RESOLUTIONS, RESOLUTIONS[0][1],
            pygame.Rect(row_x, row_y + 58, row_w, 70))
        self.resolution_hint_pos = (row_x, row_y + 58 + 72)

        row_x = self.columns[1][1].x + 18
        self.volume_slider = SliderControl(
            "music_volume", "Volume da musica", 0.7,
            pygame.Rect(row_x, row_y, row_w, 66))
        self.mute_toggle = ToggleControl(
            "music_muted", "Mudo", False,
            pygame.Rect(row_x, row_y + 84, row_w, 46))

        row_x = self.columns[2][1].x + 18
        self.speed_seg = SegmentedControl(
            "combat_speed", "Velocidade do combate", SPEEDS, 1,
            pygame.Rect(row_x, row_y, row_w, 70))
        self.damage_toggle = ToggleControl(
            "show_damage_numbers", "Numeros de dano", True,
            pygame.Rect(row_x, row_y + 82, row_w, 46))
        self.log_toggle = ToggleControl(
            "show_combat_log", "Log de combate", True,
            pygame.Rect(row_x, row_y + 134, row_w, 46))
        self.confirm_quit_toggle = ToggleControl(
            "confirm_quit", "Confirmar ao sair", True,
            pygame.Rect(row_x, row_y + 186, row_w, 46))

        self.controls = [
            self.fullscreen_toggle, self.resolution_seg,
            self.volume_slider, self.mute_toggle,
            self.speed_seg, self.damage_toggle, self.log_toggle,
            self.confirm_quit_toggle,
        ]

        self.data_panel = pygame.Rect(SAFE_MARGIN, 562, total_w, 94)
        button_y = self.data_panel.y + 24
        total_buttons = 260 + 200 + 20
        start_x = CENTER_X - total_buttons // 2
        self.reset_button = ActionButton(
            "reset_defaults", "Restaurar padroes",
            pygame.Rect(start_x, button_y, 260, 46),
            color=(120, 70, 40), font_size=20)
        self.back_button = ActionButton(
            "back", "Voltar", pygame.Rect(start_x + 280, button_y, 200, 46),
            font_size=22)

    # ------------------------------------------------------------ state

    def sync(self, settings):
        """Update every widget to reflect ``settings``."""
        self.settings = settings
        self.fullscreen_toggle.value = bool(settings.get("fullscreen", False))
        self.resolution_seg.value = list(
            settings.get("window_size", [1280, 720]))
        self.resolution_seg.enabled = not self.fullscreen_toggle.value
        self.volume_slider.value = float(settings.get("music_volume", 0.7))
        self.mute_toggle.value = bool(settings.get("music_muted", False))
        self.speed_seg.value = int(settings.get("combat_speed", 1))
        self.damage_toggle.value = bool(
            settings.get("show_damage_numbers", True))
        self.log_toggle.value = bool(settings.get("show_combat_log", True))
        self.confirm_quit_toggle.value = bool(
            settings.get("confirm_quit", True))

    # ------------------------------------------------------------ events

    def handle_event(self, event):
        if self.dialog.visible:
            result = self.dialog.handle_event(event)
            if result == "confirm":
                action = self.dialog.action
                self.dialog.close()
                return ("action", action)
            if result == "cancel":
                self.dialog.close()
            return None

        result = self.reset_button.handle_event(event)
        if result:
            self.dialog.open(action="reset_defaults")
            return None

        result = self.back_button.handle_event(event)
        if result:
            return result

        for control in self.controls:
            result = control.handle_event(event)
            if result:
                if result[0] == "setting":
                    self.settings[result[1]] = result[2]
                return result
        return None

    # ------------------------------------------------------------ draw

    def _draw_section(self, surface, rect, title):
        draw_sertao_panel(surface, rect.x, rect.y, rect.w, rect.h)
        draw_text(surface, title, (rect.x + 18, rect.y + 26),
                  font_size=24, color=SERTAO_GOLD)
        pygame.draw.line(surface, SERTAO_BORDER,
                         (rect.x + 18, rect.y + 44),
                         (rect.right - 18, rect.y + 44), 1)

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "settings")
        else:
            surface.fill((25, 18, 10))

        overlay = pygame.Surface((SCREEN_WIDTH, surface.get_height()),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 115))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "Configuracoes", (CENTER_X, 52),
                  font_size=44, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Ajustes de tela, audio e jogo", (CENTER_X, 88),
                  font_size=18, color=SERTAO_LIGHT, center=True)

        for title, rect in self.columns:
            self._draw_section(surface, rect, title)

        for control in self.controls:
            control.draw(surface)

        if not self.resolution_seg.enabled:
            draw_text(surface, "Disponivel apenas em modo janela",
                      self.resolution_hint_pos, font_size=14,
                      color=(160, 140, 110))

        self._draw_section(surface, self.data_panel, "DADOS")
        self.reset_button.draw(surface)
        self.back_button.draw(surface)

        self.dialog.draw(surface)
