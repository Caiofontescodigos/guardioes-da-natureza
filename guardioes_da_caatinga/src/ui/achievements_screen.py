"""Achievement collection screen."""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, GRAY
from src.ui.layout import (CENTER_X, SERTAO_DARK, SERTAO_PANEL, SERTAO_BORDER,
                           SERTAO_LIGHT, SERTAO_CREAM, SERTAO_GOLD,
                           SERTAO_GREEN, draw_sertao_panel, draw_sertao_button,
                           get_mouse_pos, make_back_button)
from src.ui.text import (draw_text, draw_text_centered, get_font, wrap_text)

TIER_COLORS = {
    "bronze": (205, 127, 50),
    "prata": (200, 200, 200),
    "ouro": (255, 215, 0),
    "platina": (170, 235, 255),
}

FILTERS = [
    ("TODAS", "todas"),
    ("JORNADA", "jornada"),
    ("COMBATE", "combate"),
    ("ANIMAIS", "animais"),
    ("BESTIARIO", "bestiario"),
    ("EXTRAS", "extras"),
]

CARDS_PER_PAGE = 9
CARD_W = 370
CARD_H = 145
GRID_GAP_X = 20
GRID_GAP_Y = 16
GRID_X = (SCREEN_WIDTH - (CARD_W * 3 + GRID_GAP_X * 2)) // 2
GRID_Y = 158


def draw_medal(surface, rect, category, tier, unlocked):
    rect = pygame.Rect(rect)
    color = TIER_COLORS.get(tier, SERTAO_LIGHT) if unlocked else (105, 95, 85)
    center = rect.center
    radius = rect.w // 2
    pygame.draw.circle(surface, (28, 22, 14), center, radius)
    pygame.draw.circle(surface, color, center, radius, 3)
    inner = color if unlocked else (65, 58, 50)
    pygame.draw.circle(surface, inner, center, max(2, radius - 7), 1)
    _draw_category_glyph(surface, category, center[0], center[1], color)


def _draw_category_glyph(surface, category, cx, cy, color):
    if category == "jornada":
        pygame.draw.line(surface, color, (cx - 5, cy - 13),
                         (cx - 5, cy + 14), 3)
        pygame.draw.polygon(surface, color,
                            [(cx - 4, cy - 12), (cx + 13, cy - 6),
                             (cx - 4, cy)])
    elif category == "combate":
        pygame.draw.line(surface, color, (cx, cy - 14), (cx, cy + 6), 4)
        pygame.draw.line(surface, color, (cx - 9, cy + 7),
                         (cx + 9, cy + 7), 3)
        pygame.draw.line(surface, color, (cx, cy + 8), (cx, cy + 14), 3)
    elif category == "animais":
        pygame.draw.ellipse(surface, color, (cx - 8, cy - 2, 16, 13))
        pygame.draw.circle(surface, color, (cx - 9, cy - 8), 3)
        pygame.draw.circle(surface, color, (cx - 3, cy - 12), 3)
        pygame.draw.circle(surface, color, (cx + 5, cy - 11), 3)
        pygame.draw.circle(surface, color, (cx + 11, cy - 5), 3)
    elif category == "bestiario":
        pygame.draw.rect(surface, color, (cx - 12, cy - 11, 24, 23), 2,
                         border_radius=3)
        pygame.draw.line(surface, color, (cx, cy - 10), (cx, cy + 10), 2)
        pygame.draw.line(surface, color, (cx - 8, cy - 6),
                         (cx - 2, cy - 6), 1)
        pygame.draw.line(surface, color, (cx + 2, cy - 6),
                         (cx + 8, cy - 6), 1)
    else:
        points = []
        import math
        for index in range(10):
            angle = -math.pi / 2 + index * math.pi / 5
            radius = 14 if index % 2 == 0 else 6
            points.append((cx + math.cos(angle) * radius,
                           cy + math.sin(angle) * radius))
        pygame.draw.polygon(surface, color, points)


class AchievementsScreen:
    def __init__(self, manager, assets=None):
        self.manager = manager
        self.assets = assets
        self.category = "todas"
        self.page = 0
        self.hover_filter = -1
        self.hover_card = -1
        self._build()

    def _build(self):
        width, height, gap = 150, 34, 8
        total = len(FILTERS) * width + (len(FILTERS) - 1) * gap
        start_x = CENTER_X - total // 2
        self.filter_rects = [
            pygame.Rect(start_x + index * (width + gap), 104, width, height)
            for index in range(len(FILTERS))
        ]
        self.back_button = make_back_button()
        self.prev_button = pygame.Rect(CENTER_X - 160, 652, 42, 34)
        self.next_button = pygame.Rect(CENTER_X + 118, 652, 42, 34)

    # ---------------------------------------------------------------- events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"

        if event.type == pygame.MOUSEMOTION:
            mouse = get_mouse_pos()
            self.hover_filter = -1
            for index, rect in enumerate(self.filter_rects):
                if rect.collidepoint(mouse):
                    self.hover_filter = index
                    break
            self.hover_card = self._card_at(mouse)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        mouse = get_mouse_pos()
        for index, rect in enumerate(self.filter_rects):
            if rect.collidepoint(mouse):
                self.category = FILTERS[index][1]
                self.page = 0
                return None

        if self.back_button.collidepoint(mouse):
            return "back"

        if self.prev_button.collidepoint(mouse) and self.page > 0:
            self.page -= 1
        elif (self.next_button.collidepoint(mouse)
              and self.page < self._max_page()):
            self.page += 1
        return None

    def _entries(self):
        return self.manager.get_entries(self.category)

    def _max_page(self):
        return max(0, (len(self._entries()) - 1) // CARDS_PER_PAGE)

    def _page_rects(self):
        rects = []
        entries = self._entries()
        start = self.page * CARDS_PER_PAGE
        for index in range(start, min(start + CARDS_PER_PAGE, len(entries))):
            local = index - start
            row, col = divmod(local, 3)
            rects.append(pygame.Rect(
                GRID_X + col * (CARD_W + GRID_GAP_X),
                GRID_Y + row * (CARD_H + GRID_GAP_Y),
                CARD_W, CARD_H))
        return rects

    def _card_at(self, pos):
        for index, rect in enumerate(self._page_rects()):
            if rect.collidepoint(pos):
                return index
        return -1

    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        draw_text_centered(surface, "CONQUISTAS", CENTER_X, 28, 42,
                           SERTAO_GOLD)
        self._draw_summary(surface)

        mouse = get_mouse_pos()
        for index, (label, value) in enumerate(FILTERS):
            selected = self.category == value
            hovered = selected or self.hover_filter == index
            draw_sertao_button(surface, self.filter_rects[index], label,
                               is_hovered=hovered, font_size=16)

        entries = self._entries()
        page_rects = self._page_rects()
        start = self.page * CARDS_PER_PAGE
        for local, rect in enumerate(page_rects):
            entry = entries[start + local]
            self._draw_card(surface, rect, entry,
                            local == self.hover_card)

        # Pagination
        max_page = self._max_page()
        if max_page > 0:
            draw_sertao_button(surface, self.prev_button, "<",
                               is_hovered=self.prev_button.collidepoint(mouse),
                               enabled=self.page > 0, font_size=22)
            draw_sertao_button(surface, self.next_button, ">",
                               is_hovered=self.next_button.collidepoint(mouse),
                               enabled=self.page < max_page, font_size=22)
            draw_text_centered(surface, f"Página {self.page + 1}/{max_page + 1}",
                               CENTER_X, 669, 16, SERTAO_CREAM)
        else:
            draw_text_centered(surface, "Todas as conquistas desta categoria",
                               CENTER_X, 669, 15, SERTAO_LIGHT)

        draw_sertao_button(surface, self.back_button, "Voltar",
                           is_hovered=self.back_button.collidepoint(mouse))

    def _draw_summary(self, surface):
        manager = self.manager
        unlocked = manager.unlocked_count()
        total = manager.total_achievements()
        points = int(manager.points())
        max_points = int(manager.max_points())
        title = manager.current_title()
        draw_text_centered(
            surface,
            f"{unlocked}/{total} desbloqueadas  •  {points}/{max_points} pts"
            f"  •  Título: {title}",
            CENTER_X, 64, 18, SERTAO_CREAM)

        bar = pygame.Rect(CENTER_X - 280, 82, 560, 10)
        pygame.draw.rect(surface, (35, 28, 20), bar, border_radius=5)
        fill_w = int(bar.w * manager.completion_ratio())
        if fill_w > 0:
            fill = pygame.Rect(bar.x, bar.y, fill_w, bar.h)
            pygame.draw.rect(surface, SERTAO_GOLD, fill, border_radius=5)
        pygame.draw.rect(surface, SERTAO_BORDER, bar, 1, border_radius=5)

    def _draw_card(self, surface, rect, entry, hovered):
        unlocked = entry["unlocked"]
        tier_color = TIER_COLORS.get(entry["tier"], SERTAO_LIGHT)
        border = SERTAO_GOLD if unlocked else SERTAO_BORDER
        if hovered and not unlocked:
            border = SERTAO_LIGHT
        draw_sertao_panel(surface, rect.x, rect.y, rect.w, rect.h,
                          border_color=border, alpha=235 if hovered else 220)

        medal_rect = pygame.Rect(rect.x + 18, rect.y + 18, 56, 56)
        draw_medal(surface, medal_rect, entry["category"], entry["tier"],
                   unlocked)

        secret_locked = entry["secret"] and not unlocked
        title = "???" if secret_locked else entry["name"]
        draw_text(surface, title, (rect.x + 88, rect.y + 20), font_size=20,
                  color=SERTAO_GOLD if unlocked else SERTAO_CREAM)

        tier_label = entry["tier_label"].upper()
        draw_text(surface, tier_label, (rect.right - 16, rect.y + 20),
                  font_size=13, color=tier_color if unlocked else GRAY,
                  align="right")

        description = ("Conquista secreta" if secret_locked
                       else entry["description"])
        desc_color = SERTAO_CREAM if unlocked else (175, 160, 135)
        lines = wrap_text(description, 14, rect.w - 104)[:2]
        for index, line in enumerate(lines):
            draw_text(surface, line, (rect.x + 88, rect.y + 47 + index * 17),
                      font_size=14, color=desc_color)

        progress = entry["progress"]
        bar = pygame.Rect(rect.x + 88, rect.y + rect.h - 22,
                          rect.w - 104, 8)
        if unlocked:
            draw_text(surface, "DESBLOQUEADA", (rect.x + 88,
                                                rect.y + rect.h - 35),
                      font_size=13, color=SERTAO_GREEN)
            fill_ratio = 1.0
        elif secret_locked:
            draw_text(surface, "???", (rect.x + 88, rect.y + rect.h - 35),
                      font_size=13, color=GRAY)
            fill_ratio = 0.0
        else:
            draw_text(surface, progress["text"],
                      (rect.x + 88, rect.y + rect.h - 35), font_size=13,
                      color=SERTAO_LIGHT)
            fill_ratio = progress["ratio"]

        pygame.draw.rect(surface, (35, 28, 20), bar, border_radius=4)
        fill_w = int(bar.w * max(0.0, min(1.0, fill_ratio)))
        if fill_w > 0:
            fill = pygame.Rect(bar.x, bar.y, fill_w, bar.h)
            pygame.draw.rect(surface, tier_color if unlocked else SERTAO_LIGHT,
                             fill, border_radius=4)
        pygame.draw.rect(surface, SERTAO_BORDER, bar, 1, border_radius=4)

        points_text = f"+{entry['points']} pts"
        draw_text(surface, points_text, (rect.right - 16, rect.bottom - 18),
                  font_size=14,
                  color=tier_color if unlocked else (145, 125, 95),
                  align="right")
