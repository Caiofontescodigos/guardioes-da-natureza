import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.ui.layout import (UILayout, SAFE_MARGIN, CENTER_X,
                           SERTAO_DARK, SERTAO_BORDER, SERTAO_GOLD,
                           SERTAO_CREAM, SERTAO_LIGHT, draw_sertao_panel,
                           draw_sertao_button, draw_text, get_button_metrics,
                           make_back_button, get_mouse_pos)
from src.ui.text import wrap_text


class HowToPlayScreen:
    """Tela estatica com um guia rapido de como jogar."""

    SECTIONS = [
        ("OBJETIVO",
         "Avance pelos biomas, derrote criaturas e chefes e proteja a "
         "Caatinga. Cada jornada e dividida em andares."),
        ("MAPA",
         "Escolha um ponto por andar: combate, elite, evento, acampamento, "
         "loja ou resgate. O caminho define as recompensas."),
        ("COMBATE",
         "As batalhas sao automaticas e por turnos. A velocidade define a "
         "ordem; habilidades, buffs e debuffs decidem o resultado."),
        ("EQUIPE",
         "Monte uma equipe de ate 3 animais. Cada um tem uma funcao: "
         "tanque, assassino, controle, suporte ou DPS."),
        ("ACAMPAMENTO",
         "Use o Acampamento para aplicar melhorias permanentes e "
         "reorganizar a equipe entre as jornadas."),
        ("PROGRESSO",
         "Ao atingir o nivel 6 o animal evolui para a Evolucao 1. O "
         "progresso permanente fica no save; a run atual pode ser perdida."),
        ("CONTROLES",
         "Mouse: selecionar botoes e pontos. ESC: pausar durante a run. "
         "F11: alternar entre janela e tela cheia."),
        ("DICAS",
         "Equilibre as funcoes da equipe, explore eventos e volte ao "
         "Acampamento antes de enfrentar elites e chefes."),
    ]

    def __init__(self, assets=None):
        self.assets = assets
        self.layout = UILayout()
        self.back_metrics = get_button_metrics("nav")
        self.back_button = make_back_button(self.back_metrics)
        self._build_layout()

    def _build_layout(self):
        self.panel = pygame.Rect(
            SAFE_MARGIN, self.layout.body.y - 30,
            SCREEN_WIDTH - SAFE_MARGIN * 2, self.layout.body.h - 10)

        pad = 26
        gap = 26
        inner_w = self.panel.w - pad * 2
        col_w = (inner_w - gap) // 2
        rows = (len(self.SECTIONS) + 1) // 2
        row_gap = 14
        row_h = (self.panel.h - pad * 2 - (rows - 1) * row_gap) // rows

        self.section_rects = []
        for i in range(len(self.SECTIONS)):
            col = i // rows
            row = i % rows
            x = self.panel.x + pad + col * (col_w + gap)
            y = self.panel.y + pad + row * (row_h + row_gap)
            self.section_rects.append(pygame.Rect(x, y, col_w, row_h))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                return "back"
        return None

    def _draw_section(self, surface, rect, title, body):
        draw_text(surface, title, (rect.x, rect.y + 10),
                  font_size=22, color=SERTAO_GOLD)
        pygame.draw.line(surface, SERTAO_BORDER,
                         (rect.x, rect.y + 28), (rect.right, rect.y + 28), 1)

        lines = wrap_text(body, 17, rect.w)
        y = rect.y + 46
        for line in lines:
            if y + 18 > rect.bottom:
                break
            draw_text(surface, line, (rect.x, y),
                      font_size=17, color=SERTAO_CREAM)
            y += 22

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "how_to_play")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 115))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "COMO JOGAR", (CENTER_X, 38),
                  font_size=44, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Guia rapido para a jornada", (CENTER_X, 72),
                  font_size=20, color=SERTAO_LIGHT, center=True)

        draw_sertao_panel(surface, self.panel.x, self.panel.y,
                          self.panel.w, self.panel.h, alpha=225)

        for rect, (title, body) in zip(self.section_rects, self.SECTIONS):
            self._draw_section(surface, rect, title, body)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh,
                           font_size=self.back_metrics.font_size)
