import pygame
from config import (WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN,
                    CREAM, ORANGE, PURPLE, SCREEN_WIDTH, SCREEN_HEIGHT,
                    DARK_BROWN, GOLD, load_animals, load_biomes,
                    load_enemies, load_upgrades)
from src.ui.layout import (UILayout, LayoutArea, draw_sertao_panel, draw_sertao_button,
                           draw_text, CENTER_X, CENTER_Y, SAFE_MARGIN,
                           SERTAO_DARK, SERTAO_PANEL, SERTAO_BORDER, SERTAO_LIGHT,
                           SERTAO_CREAM, SERTAO_GOLD, SERTAO_RED, SERTAO_GREEN,
                           get_mouse_pos, get_button_metrics, make_centered_column,
                           make_centered_tabs, make_back_button)
from src.ui.text import (get_font, wrap_text_chars, wrap_text, draw_text_centered,
                         draw_text_block_colored)

ANIMAL_EMOJIS = {
    "tatu_bola": "\U0001f994",
    "lobo_guara": "\U0001f98a",
    "arara_azul": "\U0001f426",
    "tamandua_bandeira": "\U0001f41c",
    "capivara": "\U0001f9ab",
    "onca_pintada": "\U0001f406",
}

ENEMY_EMOJIS = {
    "brasa": "\U0001f525",
    "chamas": "\U0001f4a5",
    "espirito_de_fogo": "\U0001f3df",
    "furacao": "\U0001f32a",
    "lobo_de_fogo": "\U0001f43a",
    "lobo_alfa_de_fogo": "\U0001f43a",
    "vendaval_de_fogo": "\U0001f32c",
}

RARITY_COLORS = {"Comum": GRAY, "Raro": BLUE, "\u00c9pico": PURPLE, "Lend\u00e1rio": SERTAO_GOLD}


class MainMenu:
    ENTRIES = [
        ("JOGAR", "play"),
        ("COMO JOGAR", "how_to_play"),
        ("BESTIARIO", "bestiary"),
        ("CONQUISTAS", "achievements"),
        ("ACAMPAMENTO", "acampamento"),
        ("CONFIGURACOES", "settings"),
        ("SAIR", "quit"),
    ]

    def __init__(self, assets=None, achievement_manager=None):
        self.assets = assets
        self.achievement_manager = achievement_manager
        self.hover_index = -1
        self.layout = UILayout()
        self._build()

    def _build(self):
        self.metrics = get_button_metrics("menu")
        rects = make_centered_column(
            len(self.ENTRIES), self.metrics,
            center_y=self.layout.body.center_y, offset_y=20)
        self.buttons = [
            {"rect": rect, "label": label, "action": action}
            for rect, (label, action) in zip(rects, self.ENTRIES)
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, b in enumerate(self.buttons):
                if b["rect"].collidepoint(event.pos):
                    self.hover_index = i
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.buttons:
                if b["rect"].collidepoint(event.pos):
                    return b["action"]
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        for i, b in enumerate(self.buttons):
            draw_sertao_button(surface, b["rect"], b["label"],
                               is_hovered=(self.hover_index == i),
                               font_size=self.metrics.font_size)

        fv = get_font(18)
        if self.achievement_manager is not None:
            title = self.achievement_manager.current_title()
            ft = get_font(16)
            title_surf = ft.render(f"Titulo: {title}", True, SERTAO_GOLD)
            title_rect = title_surf.get_rect(
                center=(CENTER_X, self.layout.footer.center_y - 10))
            surface.blit(title_surf, title_rect)
            vs = fv.render("Versao 1.0", True, GRAY)
            version_rect = vs.get_rect(
                center=(CENTER_X, self.layout.footer.center_y + 12))
            surface.blit(vs, version_rect)
        else:
            vs = fv.render("Versao 1.0", True, GRAY)
            surface.blit(vs, vs.get_rect(
                center=(CENTER_X, self.layout.footer.center_y)))


class AnimalSelectScreen:
    def __init__(self, unlocked_animals=None, assets=None, save_data=None,
                 max_selection=3, reteam_mode=False):
        self.animals = load_animals()
        self.unlocked_animals = unlocked_animals or ["tatu_bola"]
        self.save_data = save_data or {}
        self.assets = assets
        self.max_selection = max_selection
        self.reteam_mode = reteam_mode
        self.confirm_open = False
        self.hover_confirm = False
        self.selected = []
        self.hover_index = -1
        self.start_hover = False
        self.layout = UILayout()
        self._build_cards()

    def set_selection(self, ids):
        self.selected = [a for a in ids if a in self.unlocked_animals][:self.max_selection]

    def _confirm_modal_rects(self):
        return {
            "confirm": pygame.Rect(CENTER_X + 20, CENTER_Y + 90, 190, 44),
            "back": pygame.Rect(CENTER_X - 210, CENTER_Y + 90, 190, 44),
        }

    def _build_cards(self):
        self.cards = []
        animal_ids = list(self.animals.keys())
        card_w, card_h = 500, 78
        spacing = 6
        count = len(animal_ids)
        start_y = 165

        for i, aid in enumerate(animal_ids):
            x = CENTER_X - card_w // 2
            y = start_y + i * (card_h + spacing)
            self.cards.append({
                "id": aid,
                "animal": self.animals[aid],
                "rect": pygame.Rect(x, y, card_w, card_h),
                "unlocked": aid in self.unlocked_animals,
                "level": self.save_data.get("animal_data", {}).get(aid, {}).get("level", 1),
                "evolution_stage": self.save_data.get("animal_data", {}).get(aid, {}).get("evolution_stage", 0),
            })

        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)
        self.start_rect = pygame.Rect(CENTER_X - 180, 104, 360, 46)

    def handle_event(self, event):
        if self.reteam_mode and self.confirm_open:
            if event.type == pygame.MOUSEMOTION:
                rects = self._confirm_modal_rects()
                self.hover_confirm = rects["confirm"].collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = self._confirm_modal_rects()
                if rects["confirm"].collidepoint(event.pos):
                    self.confirm_open = False
                    return ("reteam_confirm", list(self.selected))
                if rects["back"].collidepoint(event.pos):
                    self.confirm_open = False
            return None

        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            self.start_hover = False
            self.hover_confirm = False
            for i, c in enumerate(self.cards):
                if c["rect"].collidepoint(event.pos) and c["unlocked"]:
                    self.hover_index = i
                    break
            if self.start_rect.collidepoint(event.pos):
                self.start_hover = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for c in self.cards:
                if c["rect"].collidepoint(event.pos) and c["unlocked"]:
                    aid = c["id"]
                    if aid in self.selected:
                        self.selected.remove(aid)
                    elif len(self.selected) < self.max_selection:
                        self.selected.append(aid)
                    return ("toggle", aid)
            if self.back_button.collidepoint(event.pos):
                return "back"
            if self.start_rect.collidepoint(event.pos) and self.selected:
                if self.reteam_mode:
                    self.confirm_open = True
                    return None
                return "start"
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "combat")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        if self.reteam_mode:
            draw_text(surface, "Escolha Novamente a Equipe", (CENTER_X, 30),
                      font_size=44, color=SERTAO_GOLD, center=True)
            draw_text(surface, "Selecione ate {} animais desbloqueados.".format(self.max_selection),
                      (CENTER_X, 62), font_size=22, color=SERTAO_CREAM, center=True)
        else:
            draw_text(surface, "Escolha Seu Animal", (CENTER_X, 30),
                      font_size=44, color=SERTAO_GOLD, center=True)
            draw_text(surface, "Selecione ate {} animais para sua jornada.".format(self.max_selection),
                      (CENTER_X, 62), font_size=22, color=SERTAO_CREAM, center=True)
        pygame.draw.line(surface, SERTAO_BORDER, (CENTER_X - 200, 88), (CENTER_X + 200, 88), 2)

        if self.reteam_mode:
            label = "CONFIRMAR NOVA EQUIPE ({}/{})".format(len(self.selected), self.max_selection)
        else:
            label = "INICIAR JORNADA ({}/{})".format(len(self.selected), self.max_selection)
        draw_sertao_button(surface, self.start_rect, label, self.start_hover,
                           enabled=bool(self.selected))

        if self.reteam_mode:
            self._draw_current_team(surface)

        for i, card in enumerate(self.cards):
            self._draw_card(surface, card, i)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)

        if self.reteam_mode and self.confirm_open:
            self._draw_reteam_confirm(surface)

    def _get_current_party(self):
        animal_map = (self.save_data or {}).get("animal_data", {}) or {}
        members = []
        for aid in self.selected[:self.max_selection]:
            info = animal_map.get(aid, {}) or {}
            animal_def = self.animals.get(aid, {})
            members.append({
                "id": aid,
                "name": animal_def.get("name", aid),
                "level": info.get("level", 1) or 1,
                "evolution_stage": info.get("evolution_stage", 0) or 0,
            })
        return members

    def _draw_current_team(self, surface):
        px = CENTER_X + 255
        panel_w = 300
        draw_text(surface, "EQUIPE ATUAL", (px + panel_w // 2, 188),
                  font_size=24, color=SERTAO_GOLD, center=True)
        members = self._get_current_party()
        stage_names = ["Base", "Evo 1"]
        row_h, gap = 72, 16
        block_h = self.max_selection * row_h + (self.max_selection - 1) * gap
        start_y = (2 * CENTER_Y - block_h) // 2 + 20
        for i in range(self.max_selection):
            row = pygame.Rect(px, start_y + i * (row_h + gap), panel_w, row_h)
            if i < len(members):
                m = members[i]
                draw_sertao_panel(surface, row.x, row.y, row.w, row.h,
                                  SERTAO_GOLD, alpha=235)
                spr = None
                if self.assets:
                    spr = self.assets.get_animal_sprite(
                        m["id"], evolution_stage=m["evolution_stage"],
                        max_width=58, max_height=58)
                if spr:
                    surface.blit(spr, spr.get_rect(midleft=(row.x + 12, row.centery)))
                else:
                    emoji = ANIMAL_EMOJIS.get(m["id"], "?")
                    draw_text(surface, emoji, (row.x + 28, row.centery),
                              font_size=36, color=SERTAO_CREAM, center=True)
                tx = row.x + 84
                stage = min(m["evolution_stage"], 1)
                draw_text(surface, m["name"], (tx, row.y + 10),
                          font_size=20, color=SERTAO_CREAM)
                draw_text(surface, "Nv.{}  [{}]".format(m["level"], stage_names[stage]),
                          (tx, row.y + 38), font_size=16, color=SERTAO_GOLD)
            else:
                draw_sertao_panel(surface, row.x, row.y, row.w, row.h,
                                  SERTAO_BORDER, alpha=210)
                draw_text(surface, "Sem animal", (row.centerx, row.centery),
                          font_size=18, color=GRAY, center=True)
        if not members:
            draw_text(surface, "Selecione os animais na lista ao lado.",
                      (px + panel_w // 2, start_y + block_h + 16),
                      font_size=15, color=SERTAO_CREAM, center=True)

    def _draw_reteam_confirm(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        pw, ph = 560, 252
        pr = pygame.Rect(CENTER_X - pw // 2, CENTER_Y - ph // 2, pw, ph)
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*SERTAO_PANEL, 248))
        surface.blit(panel, pr.topleft)
        pygame.draw.rect(surface, SERTAO_GOLD, pr, 3, border_radius=10)

        draw_text(surface, "CONFIRMAR NOVA EQUIPE?", (CENTER_X, pr.y + 40),
                  font_size=24, color=SERTAO_GOLD, center=True)
        for i, aid in enumerate(self.selected):
            anim = self.animals.get(aid, {})
            draw_text(surface, "{}.".format(i + 1) + " " + anim.get("name", aid),
                      (CENTER_X, pr.y + 80 + i * 26),
                      font_size=18, color=SERTAO_CREAM, center=True)

        rects = self._confirm_modal_rects()
        con_h = rects["confirm"].collidepoint(get_mouse_pos())
        back_h = rects["back"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["confirm"], "CONFIRMAR", con_h)
        draw_sertao_button(surface, rects["back"], "VOLTAR", back_h)

    def _draw_card(self, surface, card, index):
        r = card["rect"]
        animal = card["animal"]
        hov = (self.hover_index == index)
        selected = card["id"] in self.selected

        draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                          SERTAO_GOLD if (hov or selected) and card["unlocked"] else SERTAO_BORDER)

        if self.assets and card["unlocked"]:
            spr = self.assets.get_animal_sprite(card["id"],
                                               evolution_stage=card.get("evolution_stage", 0),
                                               max_width=50, max_height=50)
            if spr:
                surface.blit(spr, spr.get_rect(midleft=(r.x + 10, r.centery)))
            else:
                emoji = ANIMAL_EMOJIS.get(card["id"], "?")
                draw_text(surface, emoji, (r.x + 20, r.y + 14), font_size=30)

        tx = r.x + 75
        if card["unlocked"]:
            draw_text(surface, animal["name"], (tx, r.y + 6), font_size=22, color=SERTAO_CREAM)
            stage = card.get("evolution_stage", 0)
            stage_names = ["Base", "Evo 1"]
            draw_text(surface, f"Nv.{card['level']} — {stage_names[min(stage, 1)]}", (tx + 200, r.y + 8),
                      font_size=16, color=SERTAO_GOLD)
            draw_text(surface, animal["role"], (tx + 260, r.y + 8), font_size=16, color=SERTAO_LIGHT)
            s = animal["base_stats"]
            draw_text(surface, f"HP:{s['hp']}  ATK:{s['attack']}  DEF:{s['defense']}  SPD:{s['speed']}",
                      (tx, r.y + 30), font_size=14, color=SERTAO_CREAM)
            diff = "Facil" if s["hp"] >= 70 else ("Medio" if s["speed"] >= 10 else "Dificil")
            dc = GREEN if diff == "Facil" else (YELLOW if diff == "Medio" else RED)
            draw_text(surface, f"Dificuldade: {diff}", (tx, r.y + 50), font_size=14, color=dc)
            if selected:
                draw_text(surface, "\u2713", (r.right - 26, r.y + 6),
                          font_size=26, color=GREEN)
        else:
            draw_text(surface, animal["name"], (tx, r.y + 10), font_size=22, color=GRAY)
            draw_text(surface, "Bloqueado", (tx, r.y + 38), font_size=20, color=RED)


class BestiaryScreen:
    def __init__(self, save_data=None, assets=None):
        self.animals = load_animals()
        self.enemies = load_enemies()
        self.save_data = save_data or {}
        self.assets = assets
        self.animal_data = self.save_data.get("animal_data", {})
        self.unlocked_animals = self.save_data.get("unlocked_animals", [])
        self.bestiary_discovered = self.save_data.get("bestiary_discovered", [])
        self.creatures_discovered = self.save_data.get("creatures_discovered", [])
        self.animal_seen = set(self.unlocked_animals) | set(self.bestiary_discovered)
        self.tab = "ANIMAIS"
        self.selected_idx = 0
        self.hover_idx = -1
        self.layout = UILayout()
        self.tab_metrics = get_button_metrics("tab")
        self.back_metrics = get_button_metrics("nav")
        self.back_button = make_back_button(self.back_metrics)
        tabs = make_centered_tabs(2, self.tab_metrics, y=75)
        self.tab_animals, self.tab_criaturas = tabs
        self._build_grid()

    def _build_grid(self):
        self.grid_rects = []
        if self.tab == "ANIMAIS":
            ids = list(self.animals.keys())
            cell_w, cell_h = 240, 95
            cols = 3
        else:
            CREATURE_ORDER = [
                "brasa", "chamas", "espirito_de_fogo",
                "furacao", "lobo_de_fogo",
                "lobo_alfa_de_fogo", "vendaval_de_fogo"
            ]
            ids = CREATURE_ORDER
            cell_w, cell_h = 220, 85
            cols = 3

        gap_x, gap_y = 12, 12
        start_x = SAFE_MARGIN + 20
        start_y = self.layout.body.y + 120
        grid_w = cols * cell_w + (cols - 1) * gap_x
        actual_start_x = CENTER_X - grid_w // 2

        for i, eid in enumerate(ids):
            row = i // cols
            col = i % cols
            x = actual_start_x + col * (cell_w + gap_x)
            y = start_y + row * (cell_h + gap_y)
            discovered = (eid in self.animal_seen if self.tab == "ANIMAIS"
                          else eid in self.creatures_discovered)
            unlocked = eid in self.unlocked_animals if self.tab == "ANIMAIS" else True
            self.grid_rects.append({
                "id": eid,
                "rect": pygame.Rect(x, y, cell_w, cell_h),
                "discovered": discovered,
                "unlocked": unlocked,
            })

    def _get_current_ids(self):
        if self.tab == "ANIMAIS":
            return list(self.animals.keys())
        return ["brasa", "chamas", "espirito_de_fogo", "furacao", "lobo_de_fogo",
                "lobo_alfa_de_fogo", "vendaval_de_fogo"]

    def _get_selected(self):
        ids = self._get_current_ids()
        idx = min(self.selected_idx, len(ids) - 1)
        return ids[idx]

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_idx = -1
            for i, cell in enumerate(self.grid_rects):
                if cell["rect"].collidepoint(event.pos):
                    self.hover_idx = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.tab_animals.collidepoint(event.pos):
                self.tab = "ANIMAIS"
                self.selected_idx = 0
                self._build_grid()
                return None
            if self.tab_criaturas.collidepoint(event.pos):
                self.tab = "CRIATURAS"
                self.selected_idx = 0
                self._build_grid()
                return None

            for i, cell in enumerate(self.grid_rects):
                if cell["rect"].collidepoint(event.pos):
                    self.selected_idx = i
                    break
            if self.back_button.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "BESTIARIO", (CENTER_X, 30),
                  font_size=44, color=SERTAO_GOLD, center=True)

        is_animals = self.tab == "ANIMAIS"
        draw_sertao_button(surface, self.tab_animals, "ANIMAIS", is_hovered=is_animals,
                           color=SERTAO_GREEN if is_animals else SERTAO_PANEL,
                           font_size=self.tab_metrics.font_size)
        draw_sertao_button(surface, self.tab_criaturas, "CRIATURAS", is_hovered=not is_animals,
                           color=SERTAO_RED if not is_animals else SERTAO_PANEL,
                           font_size=self.tab_metrics.font_size)

        discovered_list = (list(self.animal_seen) if is_animals else self.creatures_discovered)
        total_ids = self._get_current_ids()
        total = len(total_ids)
        discovered = len([e for e in discovered_list if e in total_ids])
        pct = int((discovered / total) * 100) if total > 0 else 0

        draw_text(surface, f"Descobertas: {discovered} / {total}  ({pct}%)",
                  (CENTER_X, 200), font_size=18, color=SERTAO_CREAM, center=True)

        bar_w = 360
        bar_h = 8
        bar_x = CENTER_X - bar_w // 2
        bar_y = 220
        pygame.draw.rect(surface, (60, 45, 25), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * (discovered / total)) if total > 0 else 0
        bar_color = SERTAO_GREEN if is_animals else SERTAO_RED
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, SERTAO_BORDER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        for i, cell in enumerate(self.grid_rects):
            self._draw_cell(surface, cell, i)

        cols = 3
        if is_animals:
            cell_w = 240
        else:
            cell_w = 220
        gap_x = 12
        grid_w = cols * cell_w + (cols - 1) * gap_x
        detail_x = CENTER_X + grid_w // 2 + 20
        detail_w = SCREEN_WIDTH - detail_x - SAFE_MARGIN - 10
        detail_y = self.layout.body.y + 120
        detail_h = SCREEN_HEIGHT - detail_y - 80

        if detail_w > 100:
            self._draw_detail_panel(surface, detail_x, detail_y, detail_w, detail_h)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh,
                           font_size=self.back_metrics.font_size)

    def _draw_cell(self, surface, cell, index):
        r = cell["rect"]
        is_hovered = (self.hover_idx == index)
        is_selected = (self.selected_idx == index)
        discovered = cell["discovered"]

        if is_selected:
            border_c = SERTAO_GOLD
        elif is_hovered:
            border_c = SERTAO_LIGHT
        else:
            border_c = SERTAO_BORDER

        if discovered:
            if self.tab == "ANIMAIS":
                unlocked = cell["unlocked"]
                if unlocked:
                    bg = (45, 55, 35) if not is_hovered else (55, 70, 45)
                else:
                    bg = (50, 45, 30)
            else:
                enemy_data = self.enemies.get(cell["id"], {})
                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)
                if is_boss:
                    bg = (60, 30, 30) if not is_hovered else (75, 40, 40)
                elif is_elite:
                    bg = (55, 45, 25) if not is_hovered else (70, 55, 35)
                else:
                    bg = (45, 35, 25) if not is_hovered else (55, 45, 35)
        else:
            bg = (30, 25, 18)

        pygame.draw.rect(surface, bg, r, border_radius=10)
        pygame.draw.rect(surface, border_c, r, 2, border_radius=10)

        sprite_cy = r.y + 24 if self.tab == "ANIMAIS" else r.y + 21
        if self.tab == "ANIMAIS":
            animal = self.animals.get(cell["id"], {})
            stage = self.animal_data.get(cell["id"], {}).get("evolution_stage", 0)
            stage_tags = ["", " [Evo 1]"]
            if discovered:
                spr = None
                if self.assets and cell.get("unlocked"):
                    spr = self.assets.get_animal_sprite(cell["id"],
                                                       evolution_stage=stage,
                                                       max_width=36, max_height=36)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.centerx, sprite_cy)))
                else:
                    emoji_color = (SERTAO_CREAM if cell.get("unlocked")
                                   else (140, 120, 90))
                    draw_text_centered(surface, ANIMAL_EMOJIS.get(cell["id"], "?"),
                                       r.centerx, sprite_cy, 24, emoji_color)

                name = animal.get("name", cell["id"])
                tag = stage_tags[min(stage, 1)]
                draw_text_centered(surface, name + tag, r.centerx, r.y + 50,
                                   15, SERTAO_CREAM)
                draw_text_centered(surface, animal.get("role", ""), r.centerx,
                                   r.y + 66, 12, SERTAO_LIGHT)
                rarity = animal.get("rarity", "")
                rc = RARITY_COLORS.get(rarity, GRAY)
                draw_text_centered(surface, rarity, r.centerx, r.y + 79,
                                   11, rc)
                if cell.get("unlocked"):
                    draw_text_centered(surface, "\u2713", r.right - 14, r.y + 10,
                                       16, GREEN)
            else:
                draw_text_centered(surface, "\U0001f512", r.centerx, sprite_cy,
                                   22, (60, 50, 40))
                draw_text_centered(surface, "???", r.centerx, r.y + 52,
                                   18, (60, 50, 40))
        else:
            enemy_data = self.enemies.get(cell["id"], {})
            emoji = ENEMY_EMOJIS.get(cell["id"], "\U0001f525")
            if discovered:
                spr = None
                if self.assets:
                    spr = self.assets.get_enemy_sprite(cell["id"],
                                                       max_width=36, max_height=36)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.centerx, sprite_cy)))
                else:
                    draw_text_centered(surface, emoji, r.centerx, sprite_cy,
                                       24, SERTAO_CREAM)

                name = enemy_data.get("name", cell["id"])
                draw_text_centered(surface, name, r.centerx, r.y + 47,
                                   15, SERTAO_CREAM)

                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)
                tag = "CHEFE" if is_boss else ("ELITE" if is_elite else "Comum")
                tag_color = SERTAO_RED if is_boss else (ORANGE if is_elite else GRAY)
                region = enemy_data.get("region", "")
                tag_line = tag + ((" · " + region) if region else "")
                draw_text_centered(surface, tag_line, r.centerx, r.y + 63,
                                   12, tag_color)
            else:
                draw_text_centered(surface, "\U0001f512", r.centerx, sprite_cy,
                                   22, (60, 50, 40))
                draw_text_centered(surface, "???", r.centerx, r.y + 51,
                                   18, (60, 50, 40))

    def _draw_detail_panel(self, surface, x, y, w, h):
        draw_sertao_panel(surface, x, y, w, h)
        selected_id = self._get_selected()
        px = x + 15
        py = y + 15

        if self.tab == "ANIMAIS":
            animal = self.animals.get(selected_id, {})
            discovered = selected_id in self.animal_seen if self.tab == "ANIMAIS" else selected_id in self.creatures_discovered
            unlocked = selected_id in self.unlocked_animals
            saved = self.animal_data.get(selected_id, {})
            stage = saved.get("evolution_stage", 0)
            stage_tags = ["", " — Evolucao 1"]
            stage_name = stage_tags[min(stage, 1)]

            if discovered:
                if self.assets and unlocked:
                    spr = self.assets.get_animal_sprite(selected_id,
                                                       evolution_stage=stage,
                                                       max_width=55, max_height=55)
                    if spr:
                        surface.blit(spr, spr.get_rect(topleft=(px, py)))
                    else:
                        icon_rect = pygame.Rect(px, py, 55, 55)
                        pygame.draw.rect(surface, SERTAO_GREEN, icon_rect, border_radius=10)
                else:
                    icon_rect = pygame.Rect(px, py, 55, 55)
                    pygame.draw.rect(surface, SERTAO_GREEN if unlocked else GRAY, icon_rect, border_radius=10)

                draw_text(surface, animal.get("name", "") + stage_name, (px + 65, py + 5),
                          font_size=20, color=SERTAO_CREAM)
                draw_text(surface, animal.get("role", ""), (px + 65, py + 30),
                          font_size=16, color=SERTAO_LIGHT)
                rarity = animal.get("rarity", "")
                rc = RARITY_COLORS.get(rarity, GRAY)
                draw_text(surface, rarity, (px + 65, py + 50), font_size=14, color=rc)

                py += 70
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                desc_lines = wrap_text_chars(animal.get("description", ""), 32)
                for line in desc_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                if unlocked and saved:
                    draw_text(surface, "Status Reais:", (px, py), font_size=16, color=SERTAO_GOLD)
                    py += 20
                    stats = [
                        (f"HP: {saved.get('max_hp', 0)}", GREEN),
                        (f"ATK: {saved.get('base_attack', 0)}", RED),
                        (f"DEF: {saved.get('base_defense', 0)}", BLUE),
                        (f"SPD: {saved.get('base_speed', 0)}", YELLOW),
                        (f"Crit: {saved.get('crit_chance', 0)}%", PURPLE),
                        (f"Dodge: {saved.get('dodge', 0)}%", ORANGE),
                    ]
                    for stat_text, stat_color in stats:
                        draw_text(surface, stat_text, (px, py), font_size=14, color=stat_color)
                        py += 18
                    py += 5
                    draw_text(surface, f"XP: {saved.get('xp', 0)} / {saved.get('xp_to_level', 100)}",
                              (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18
                    upgrade_id = saved.get("specific_upgrade_id")
                    if upgrade_id:
                        py += 5
                        pygame.draw.line(surface, SERTAO_BORDER,
                                         (px, py), (x + w - 15, py), 1)
                        py += 8
                        draw_text(surface, "MELHORIA ESPECIFICA:",
                                  (px, py), font_size=16, color=SERTAO_GOLD)
                        py += 20
                        from src.entities.animal import SPECIFIC_UPGRADES
                        for udata in SPECIFIC_UPGRADES.values():
                            if udata["id"] == upgrade_id:
                                draw_text(surface,
                                          f"{udata['icon']} {udata['name']}",
                                          (px, py), font_size=15, color=GREEN)
                                py += 18
                                udesc_lines = wrap_text_chars(
                                    udata.get("description", ""), 32)
                                for line in udesc_lines[:3]:
                                    draw_text(surface, line, (px, py),
                                              font_size=12,
                                              color=SERTAO_CREAM)
                                    py += 16
                                break
                else:
                    draw_text(surface, "Status Base:", (px, py), font_size=16, color=SERTAO_GOLD)
                    py += 20
                    s = animal.get("base_stats", {})
                    stats = [
                        (f"HP: {s.get('hp', 0)}", GREEN),
                        (f"ATK: {s.get('attack', 0)}", RED),
                        (f"DEF: {s.get('defense', 0)}", BLUE),
                        (f"SPD: {s.get('speed', 0)}", YELLOW),
                        (f"Crit: {s.get('crit_chance', 0)}%", PURPLE),
                        (f"Dodge: {s.get('dodge', 0)}%", ORANGE),
                    ]
                    for stat_text, stat_color in stats:
                        draw_text(surface, stat_text, (px, py), font_size=14, color=stat_color)
                        py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                draw_text(surface, "COMO RESGATAR:", (px, py), font_size=16, color=SERTAO_GOLD)
                py += 20
                rescue = animal.get("rescue_description", "Derrote o chefe da regiao.")
                rescue_lines = wrap_text_chars(rescue, 32)
                for line in rescue_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                if unlocked:
                    py += 6
                    draw_text(surface, "\u2713 Resgatado!", (px, py), font_size=16, color=GREEN)
            else:
                draw_text(surface, "???", (px + 10, py + 10), font_size=28, color=GRAY)
                draw_text(surface, "Nao Descoberto", (px + 10, py + 45),
                          font_size=18, color=(120, 100, 70))
                py += 80
                pygame.draw.line(surface, (80, 60, 40), (px, py), (x + w - 15, py), 1)
                py += 12
                draw_text(surface, "Encontre este animal para", (px, py), font_size=14, color=(100, 80, 60))
                py += 18
                draw_text(surface, "desbloquear sua ficha.", (px, py), font_size=14, color=(100, 80, 60))
        else:
            enemy_data = self.enemies.get(selected_id, {})
            discovered = selected_id in self.creatures_discovered

            if discovered:
                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)

                if self.assets:
                    spr = self.assets.get_enemy_sprite(selected_id, max_width=55, max_height=55)
                    if spr:
                        surface.blit(spr, spr.get_rect(topleft=(px, py)))
                    else:
                        icon_color = SERTAO_RED if is_boss else (ORANGE if is_elite else SERTAO_CREAM)
                        icon_rect = pygame.Rect(px, py, 55, 55)
                        pygame.draw.rect(surface, icon_color, icon_rect, border_radius=10)
                else:
                    icon_color = SERTAO_RED if is_boss else (ORANGE if is_elite else SERTAO_CREAM)
                    icon_rect = pygame.Rect(px, py, 55, 55)
                    pygame.draw.rect(surface, icon_color, icon_rect, border_radius=10)

                draw_text(surface, enemy_data.get("name", selected_id), (px + 65, py + 5),
                          font_size=22, color=SERTAO_CREAM)
                tag = "CHEFE" if is_boss else ("ELITE" if is_elite else "Comum")
                tag_color = SERTAO_RED if is_boss else (ORANGE if is_elite else GRAY)
                draw_text(surface, tag, (px + 65, py + 30), font_size=16, color=tag_color)

                py += 70
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                desc = enemy_data.get("description", "")
                desc_lines = wrap_text_chars(desc, 32)
                for line in desc_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                draw_text(surface, "Status Base:", (px, py), font_size=16, color=SERTAO_GOLD)
                py += 20
                s = enemy_data.get("stats", {})
                stats = [
                    (f"HP: {s.get('hp', 0)}", GREEN),
                    (f"ATK: {s.get('attack', 0)}", RED),
                    (f"DEF: {s.get('defense', 0)}", BLUE),
                    (f"SPD: {s.get('speed', 0)}", YELLOW),
                    (f"Crit: {s.get('crit_chance', 0)}%", PURPLE),
                    (f"Dodge: {s.get('dodge', 0)}%", ORANGE),
                ]
                for stat_text, stat_color in stats:
                    draw_text(surface, stat_text, (px, py), font_size=14, color=stat_color)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                draw_text(surface, "Regiao:", (px, py), font_size=16, color=SERTAO_GOLD)
                py += 20
                draw_text(surface, enemy_data.get("region", "Desconhecida"), (px, py),
                          font_size=16, color=SERTAO_CREAM)

                if is_boss:
                    py += 25
                    pygame.draw.line(surface, SERTAO_RED, (px, py), (x + w - 15, py), 1)
                    py += 8
                    draw_text(surface, "Protege:", (px, py), font_size=14, color=SERTAO_GOLD)
                    py += 18
                    biomes = load_biomes()
                    animals = load_animals()
                    for bid, bdata in biomes.items():
                        if selected_id in bdata.get("bosses", []):
                            rescue = bdata.get("rescue_animal", "")
                            if rescue:
                                rname = animals.get(rescue, {}).get("name", rescue)
                                draw_text(surface, rname, (px, py), font_size=14, color=GREEN)
                                py += 18
            else:
                draw_text(surface, "???", (px + 10, py + 10), font_size=28, color=(60, 50, 40))
                draw_text(surface, "Criatura Desconhecida", (px + 10, py + 45),
                          font_size=18, color=(80, 70, 50))
                py += 80
                pygame.draw.line(surface, (80, 60, 40), (px, py), (x + w - 15, py), 1)
                py += 12
                draw_text(surface, "Derrote esta criatura para", (px, py),
                          font_size=14, color=(100, 80, 60))
                py += 18
                draw_text(surface, "desbloquear sua ficha.", (px, py),
                          font_size=14, color=(100, 80, 60))


class AcampamentoScreen:
    SECTIONS = ["MELHORIAS", "EQUIPE"]
    STAGE_NAMES = ["Base", "Evo 1"]

    def __init__(self, save_data=None, assets=None, party=None):
        self.save_data = save_data or {}
        self.assets = assets
        self.party = party or []
        self.animals = load_animals()
        self.upgrades_data = load_upgrades()
        self.unlocked = self.save_data.get("unlocked_animals", [])
        self.sel_section = 0
        self.sel_animal = 0
        self.hover_item = -1
        self.layout = UILayout()
        self._build_tabs()

    def _build_tabs(self):
        self.tab_metrics = get_button_metrics("tab")
        self.back_metrics = get_button_metrics("nav")
        self.tab_rects = make_centered_tabs(len(self.SECTIONS), self.tab_metrics, y=75)
        self.back_button = make_back_button(self.back_metrics)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, tab in enumerate(self.tab_rects):
                if tab.collidepoint(event.pos):
                    self.sel_section = i
                    return None

            if self.back_button.collidepoint(event.pos):
                return ("back", None)

            if self.sel_section == 0:
                return self._handle_melhorias_events(event)
            elif self.sel_section == 1:
                return self._handle_equipe_events(event)

        if event.type == pygame.MOUSEMOTION:
            self.hover_item = -1

        return None

    def _handle_melhorias_events(self, event):
        return None

    def _handle_equipe_events(self, event):
        rects = self._get_party_rects()
        for i in range(len(self.party)):
            if i < len(rects) and rects[i].collidepoint(event.pos):
                self.sel_animal = i
        return None

    def _get_party_rects(self):
        bw, bh = 500, 60
        gap = 10
        sy = 170
        rects = []
        for i in range(len(self.party)):
            x = CENTER_X - bw // 2
            y = sy + i * (bh + gap)
            rects.append(pygame.Rect(x, y, bw, bh))
        return rects

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "ACAMPAMENTO", (CENTER_X, 30),
                  font_size=44, color=SERTAO_GOLD, center=True)
        pygame.draw.line(surface, SERTAO_BORDER, (CENTER_X - 170, 62), (CENTER_X + 170, 62), 2)

        for i, tab in enumerate(self.tab_rects):
            is_sel = (i == self.sel_section)
            draw_sertao_button(surface, tab, self.SECTIONS[i], is_hovered=is_sel,
                               color=SERTAO_GREEN if is_sel else SERTAO_PANEL,
                               font_size=self.tab_metrics.font_size)

        if self.sel_section == 0:
            self._draw_melhorias_section(surface)
        elif self.sel_section == 1:
            self._draw_equipe_section(surface)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh,
                           font_size=self.back_metrics.font_size)

    def _draw_melhorias_section(self, surface):
        draw_text(surface, "Melhorias permanentes dos animais",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
            return

        animal = self.party[min(self.sel_animal, len(self.party) - 1)]
        upgrades = load_upgrades()

        y = 180
        for uid, udata in upgrades.items():
            btn = pygame.Rect(CENTER_X - 250, y, 500, 48)
            draw_sertao_panel(surface, btn.x, btn.y, btn.w, btn.h)
            emoji = "\u2694\ufe0f" if udata.get("category") == "offense" else "\U0001f6e1"
            draw_text(surface, f"{emoji} {udata['name']}", (btn.x + 15, btn.y + 8),
                      font_size=18, color=SERTAO_CREAM)
            draw_text(surface, udata.get("description", ""), (btn.x + 15, btn.y + 28),
                      font_size=13, color=SERTAO_LIGHT)
            y += 56

    def _draw_equipe_section(self, surface):
        draw_text(surface, "Equipe atual (max 3)",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
            return

        rects = self._get_party_rects()
        animal_data = self.save_data.get("animal_data", {})
        for i, member in enumerate(self.party):
            if i >= len(rects):
                break
            r = rects[i]
            is_hov = (self.hover_item == i)
            draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                              SERTAO_GOLD if is_hov else SERTAO_BORDER)

            stage = animal_data.get(member.animal_id, {}).get("evolution_stage", 0)
            if self.assets:
                spr = self.assets.get_animal_sprite(member.animal_id,
                                                   evolution_stage=stage,
                                                   max_width=44, max_height=44)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.x + 30, r.centery)))
                else:
                    emoji = ANIMAL_EMOJIS.get(member.animal_id, "?")
                    draw_text(surface, emoji, (r.x + 12, r.y + 8), font_size=28)
            else:
                emoji = ANIMAL_EMOJIS.get(member.animal_id, "?")
                draw_text(surface, emoji, (r.x + 12, r.y + 8), font_size=28)

            form_name = self.STAGE_NAMES[min(stage, 1)]
            draw_text(surface, f"{member.name} [{form_name}]", (r.x + 65, r.y + 8),
                      font_size=18, color=SERTAO_CREAM)
            draw_text(surface, member.role, (r.x + 65, r.y + 28), font_size=14, color=SERTAO_LIGHT)
            draw_text(surface, f"Lv.{member.level}  HP:{member.hp}/{member.max_hp}  ATK:{member.attack} DEF:{member.defense} SPD:{member.speed}",
                      (r.x + 65, r.y + 45), font_size=13, color=SERTAO_GOLD)


class BiomeSelectScreen:
    def __init__(self, unlocked_biomes=None, assets=None):
        self.biomes = load_biomes()
        self.unlocked_biomes = unlocked_biomes or ["caatinga"]
        self.selected_biome = None
        self.assets = assets
        self.hover_index = -1
        self.layout = UILayout()
        self._build()

    def _build(self):
        self.buttons = []
        bw, bh = 600, 72
        gap = 12
        count = len(self.biomes)
        total = count * bh + (count - 1) * gap
        sy = self.layout.body.y + (self.layout.body.h - total) // 2

        for i, (bid, biome) in enumerate(self.biomes.items()):
            x = CENTER_X - bw // 2
            y = sy + i * (bh + gap)
            self.buttons.append({
                "id": bid, "biome": biome,
                "rect": pygame.Rect(x, y, bw, bh),
                "unlocked": bid in self.unlocked_biomes,
            })

        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, b in enumerate(self.buttons):
                if b["rect"].collidepoint(event.pos) and b["unlocked"]:
                    self.hover_index = i
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.buttons:
                if b["rect"].collidepoint(event.pos) and b["unlocked"]:
                    return b["id"]
            if self.back_button.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "biome_select")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "Selecione o Bioma", (CENTER_X, 50),
                  font_size=44, color=SERTAO_GOLD, center=True)

        for i, b in enumerate(self.buttons):
            r = b["rect"]
            hov = (self.hover_index == i)
            if b["unlocked"]:
                bc = b["biome"]["color"]
                if hov:
                    bc = tuple(min(255, c + 30) for c in bc)
                pygame.draw.rect(surface, bc, r, border_radius=10)
                bdr = SERTAO_GOLD if hov else WHITE
            else:
                pygame.draw.rect(surface, DARK_GRAY, r, border_radius=10)
                bdr = GRAY
            pygame.draw.rect(surface, bdr, r, 2, border_radius=10)

            draw_text(surface, b["biome"]["name"], (r.x + 20, r.y + 15),
                      font_size=26, color=SERTAO_CREAM)
            draw_text(surface, b["biome"]["description"], (r.x + 20, r.y + 48),
                      font_size=17, color=SERTAO_CREAM)
            if not b["unlocked"]:
                draw_text(surface, "Bloqueado", (r.right - 100, r.y + 28),
                          font_size=22, color=RED)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)


class CageRewardScreen:
    def __init__(self, animal_data=None, assets=None):
        self.animal_data = animal_data
        self.assets = assets
        self.layout = UILayout()
        self.anim_timer = 0
        self.revealed = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.revealed:
                self.revealed = True
                self.anim_timer = 0
                return None
            return "continue"
        return None

    def update(self):
        if not self.revealed:
            self.anim_timer += 1

    def draw(self, surface):
        surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 400
        panel_x = CENTER_X - panel_w // 2
        panel_y = CENTER_Y - panel_h // 2
        draw_sertao_panel(surface, panel_x, panel_y, panel_w, panel_h, SERTAO_GOLD)

        if not self.revealed:
            draw_text(surface, "\U0001faa4", (CENTER_X, CENTER_Y - 60),
                      font_size=80, color=SERTAO_GOLD, center=True)
            draw_text(surface, "JAULA MISTERIOSA", (CENTER_X, CENTER_Y + 40),
                      font_size=32, color=SERTAO_GOLD, center=True)
            draw_text(surface, "Clique para abrir...", (CENTER_X, CENTER_Y + 80),
                      font_size=20, color=SERTAO_CREAM, center=True)
        else:
            if self.animal_data:
                aid = self.animal_data.get("id", "")
                draw_text(surface, "\U0001f389", (CENTER_X, CENTER_Y - 100),
                          font_size=50, color=SERTAO_GOLD, center=True)
                draw_text(surface, "NOVO ANIMAL LIBERTADO!", (CENTER_X, CENTER_Y - 40),
                          font_size=28, color=SERTAO_GOLD, center=True)

                if self.assets:
                    spr = self.assets.get_animal_sprite(aid, max_width=100, max_height=100)
                    if spr:
                        surface.blit(spr, spr.get_rect(center=(CENTER_X, CENTER_Y + 20)))
                    else:
                        emoji = ANIMAL_EMOJIS.get(aid, "?")
                        draw_text(surface, emoji, (CENTER_X, CENTER_Y + 20),
                                  font_size=60, color=SERTAO_CREAM, center=True)
                else:
                    emoji = ANIMAL_EMOJIS.get(aid, "?")
                    draw_text(surface, emoji, (CENTER_X, CENTER_Y + 20),
                              font_size=60, color=SERTAO_CREAM, center=True)

                draw_text(surface, self.animal_data.get("name", aid), (CENTER_X, CENTER_Y + 80),
                          font_size=28, color=SERTAO_CREAM, center=True)
                draw_text(surface, self.animal_data.get("role", ""), (CENTER_X, CENTER_Y + 110),
                          font_size=20, color=SERTAO_LIGHT, center=True)
            else:
                draw_text(surface, "A jaula estava vazia...", (CENTER_X, CENTER_Y),
                          font_size=28, color=GRAY, center=True)

            draw_text(surface, "Clique para continuar", (CENTER_X, CENTER_Y + 160),
                      font_size=18, color=SERTAO_CREAM, center=True)


class JourneySelectScreen:
    def __init__(self, save_manager, assets=None):
        self.save_manager = save_manager
        self.assets = assets
        self.layout = UILayout()
        self.hover_slot = -1
        self.corrupt_slot = None
        self.confirm_slot = None
        self.action_slot = None
        self._refresh()

    def _refresh(self):
        self.info_cache = {}
        self.corrupt_cache = {}
        for s in range(1, 4):
            status = self.save_manager.get_slot_status(s)
            if status == "corrupt":
                self.corrupt_cache[s] = True
                self.info_cache[s] = None
            elif status == "ok":
                self.info_cache[s] = self.save_manager.get_slot_info(s)
            else:
                self.info_cache[s] = None
        self.slot_rects = []
        btn_w, btn_h = 480, 164
        spacing = 12
        start_y = self.layout.body.y + 18
        for i in range(3):
            x = CENTER_X - btn_w // 2
            y = start_y + i * (btn_h + spacing)
            self.slot_rects.append(pygame.Rect(x, y, btn_w, btn_h))
        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)

    def _slot_buttons(self, r):
        select_btn = pygame.Rect(r.right - 150, r.centery - 20, 130, 40)
        new_btn = pygame.Rect(r.right - 170, r.y + (r.h - 38) // 2, 145, 38)
        return select_btn, new_btn

    def _action_options(self, has_run):
        options = []
        if has_run:
            options.append("continue")
        options.extend(["reteam", "delete", "back"])
        return options

    def _action_modal_rects(self, has_run):
        options = self._action_options(has_run)
        btn_w, btn_h, gap = 340, 46, 14
        content_h = len(options) * btn_h + (len(options) - 1) * gap
        title_h = 34
        sub_h = 24
        padding_top = 24
        padding_bottom = 24
        separation = 30
        panel_w = 620
        panel_h = padding_top + title_h + sub_h + separation + content_h + padding_bottom
        px = CENTER_X - panel_w // 2
        py = CENTER_Y - panel_h // 2

        rects = {}
        y = py + padding_top + title_h + sub_h + separation
        for i, opt in enumerate(options):
            rects[opt] = pygame.Rect(CENTER_X - btn_w // 2, y + i * (btn_h + gap),
                                     btn_w, btn_h)
        return rects, panel_w, panel_h

    def _corrupt_modal_rects(self):
        cy = CENTER_Y + 70
        return {
            "recover": pygame.Rect(CENTER_X - 280, cy, 165, 42),
            "delete": pygame.Rect(CENTER_X - 85, cy, 160, 42),
            "cancel": pygame.Rect(CENTER_X + 105, cy, 160, 42),
        }

    def _confirm_modal_rects(self):
        return {
            "cancel": pygame.Rect(CENTER_X - 210, CENTER_Y + 85, 190, 42),
            "delete": pygame.Rect(CENTER_X + 20, CENTER_Y + 85, 190, 42),
        }

    def is_corrupt(self, slot):
        return self.save_manager.get_slot_status(slot) == "corrupt"

    def handle_event(self, event):
        if self.confirm_slot is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = self._confirm_modal_rects()
                if rects["cancel"].collidepoint(event.pos):
                    self.confirm_slot = None
                elif rects["delete"].collidepoint(event.pos):
                    slot = self.confirm_slot
                    self.confirm_slot = None
                    self.save_manager.delete_slot(slot)
                    self._refresh()
                    return ("deleted", slot)
            return None

        if self.corrupt_slot is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = self._corrupt_modal_rects()
                slot = self.corrupt_slot
                if rects["recover"].collidepoint(event.pos):
                    recovered = self.save_manager.restore_save(slot)
                    self._refresh()
                    if recovered:
                        self.corrupt_slot = None
                        return ("continue", slot)
                elif rects["delete"].collidepoint(event.pos):
                    self.corrupt_slot = None
                    self.save_manager.delete_slot(slot)
                    self._refresh()
                    return ("deleted", slot)
                elif rects["cancel"].collidepoint(event.pos):
                    self.corrupt_slot = None
            return None

        if self.action_slot is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                slot = self.action_slot
                info = self.info_cache.get(slot)
                has_run = bool(info and info.get("run_active"))
                rects, _, _ = self._action_modal_rects(has_run)

                if has_run and rects["continue"].collidepoint(event.pos):
                    self.action_slot = None
                    return ("continue", slot)
                if rects["reteam"].collidepoint(event.pos):
                    self.action_slot = None
                    return ("reteam", slot)
                if rects["delete"].collidepoint(event.pos):
                    self.action_slot = None
                    self.confirm_slot = slot
                    return None
                if rects["back"].collidepoint(event.pos):
                    self.action_slot = None
            return None

        if event.type == pygame.MOUSEMOTION:
            self.hover_slot = -1
            for i, r in enumerate(self.slot_rects):
                if r.collidepoint(event.pos):
                    self.hover_slot = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                return "back"
            for i, r in enumerate(self.slot_rects):
                if not r.collidepoint(event.pos):
                    continue
                slot = i + 1
                if self.corrupt_cache.get(slot):
                    self.corrupt_slot = slot
                    return None
                select_btn, new_btn = self._slot_buttons(r)
                info = self.info_cache.get(slot)
                if info:
                    self.action_slot = slot
                else:
                    if new_btn.collidepoint(event.pos):
                        return ("new", slot)
                return None
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "combat")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "ESCOLHER JORNADA", (CENTER_X, self.layout.header.center_y),
                  font_size=40, color=SERTAO_GOLD, center=True)

        for i in range(3):
            slot = i + 1
            info = self.info_cache.get(slot)
            corrupt = self.corrupt_cache.get(slot, False)
            self._draw_slot(surface, slot, info, i, corrupt)

        if self.corrupt_slot is not None:
            self._draw_corrupt_msg(surface)
        elif self.confirm_slot is not None:
            self._draw_confirm_msg(surface)
        elif self.action_slot is not None:
            self._draw_action_msg(surface)

        bh = self.back_button.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)

    def _draw_modal_backdrop(self, surface, pw, ph, border_color=SERTAO_RED):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        pr = pygame.Rect(CENTER_X - pw // 2, CENTER_Y - ph // 2, pw, ph)
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*SERTAO_PANEL, 248))
        surface.blit(panel, pr.topleft)
        pygame.draw.rect(surface, border_color, pr, 3, border_radius=10)
        return pr

    def _draw_confirm_msg(self, surface):
        pw, ph = 500, 210
        pr = self._draw_modal_backdrop(surface, pw, ph)

        draw_text(surface, "Apagar esta jornada?", (CENTER_X, pr.y + 55),
                  font_size=26, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Todo o progresso deste slot", (CENTER_X, pr.y + 95),
                  font_size=18, color=SERTAO_CREAM, center=True)
        draw_text(surface, "sera perdido.", (CENTER_X, pr.y + 118),
                  font_size=18, color=SERTAO_CREAM, center=True)

        rects = self._confirm_modal_rects()
        cancel_h = rects["cancel"].collidepoint(get_mouse_pos())
        delete_h = rects["delete"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["cancel"], "CANCELAR", cancel_h)
        draw_sertao_button(surface, rects["delete"], "APAGAR", delete_h)

    def _draw_action_msg(self, surface):
        info = self.info_cache.get(self.action_slot)
        has_run = bool(info and info.get("run_active"))
        rects, pw, ph = self._action_modal_rects(has_run)
        pr = self._draw_modal_backdrop(surface, pw, ph, border_color=SERTAO_BORDER)

        draw_text(surface, "ESCOLHER A\u00c7\u00c3O", (CENTER_X, pr.y + 40),
                  font_size=26, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Como deseja entrar nesta jornada?",
                  (CENTER_X, pr.y + 68), font_size=16, color=SERTAO_CREAM, center=True)

        if has_run:
            cont_h = rects["continue"].collidepoint(get_mouse_pos())
            draw_sertao_button(surface, rects["continue"], "CONTINUAR RUN", cont_h)
        ret_h = rects["reteam"].collidepoint(get_mouse_pos())
        del_h = rects["delete"].collidepoint(get_mouse_pos())
        back_h = rects["back"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["reteam"], "ESCOLHER NOVAMENTE A EQUIPE", ret_h)
        draw_sertao_button(surface, rects["delete"], "APAGAR SAVE", del_h,
                           color=(90, 40, 40) if not del_h else (120, 55, 55))
        draw_sertao_button(surface, rects["back"], "VOLTAR", back_h)

    def _draw_corrupt_msg(self, surface):
        pw, ph = 540, 230
        pr = self._draw_modal_backdrop(surface, pw, ph)

        draw_text(surface, "\u26a0", (CENTER_X, pr.y + 34),
                  font_size=34, color=SERTAO_RED, center=True)
        draw_text(surface, "SAVE CORROMPIDO", (CENTER_X, pr.y + 74),
                  font_size=26, color=SERTAO_RED, center=True)
        draw_text(surface, "O arquivo nao pode ser carregado.",
                  (CENTER_X, pr.y + 108), font_size=17, color=SERTAO_CREAM, center=True)
        draw_text(surface, "Tente recuperar um backup ou apague o slot.",
                  (CENTER_X, pr.y + 132), font_size=15, color=SERTAO_CREAM, center=True)

        rects = self._corrupt_modal_rects()
        rec_h = rects["recover"].collidepoint(get_mouse_pos())
        del_h = rects["delete"].collidepoint(get_mouse_pos())
        can_h = rects["cancel"].collidepoint(get_mouse_pos())
        draw_sertao_button(surface, rects["recover"], "TENTAR RECUPERAR", rec_h)
        draw_sertao_button(surface, rects["delete"], "APAGAR", del_h)
        draw_sertao_button(surface, rects["cancel"], "VOLTAR", can_h)

    def _draw_slot(self, surface, slot, info, index, corrupt=False):
        r = self.slot_rects[index]
        is_hover = self.hover_slot == index

        if corrupt:
            border_color = SERTAO_RED
            bg = (60, 40, 30) if not is_hover else (75, 50, 40)
        else:
            if is_hover:
                border_color = SERTAO_GOLD
                bg = (50, 40, 25)
            else:
                border_color = SERTAO_BORDER
                bg = SERTAO_PANEL

        panel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        panel.fill((*bg, 220))
        surface.blit(panel, r.topleft)
        pygame.draw.rect(surface, border_color, r, 2, border_radius=8)

        select_btn, new_btn = self._slot_buttons(r)

        if corrupt:
            draw_text(surface, f"SAVE {slot}", (r.x + 22, r.y + 12),
                      font_size=26, color=SERTAO_GOLD)
            draw_text(surface, "\u26a0 SAVE CORROMPIDO", (r.x + 22, r.y + 52),
                      font_size=20, color=SERTAO_RED)
            draw_text(surface, "Clique para recuperar ou apagar", (r.x + 22, r.y + 84),
                      font_size=14, color=GRAY)
        elif info:
            draw_text(surface, f"SAVE {slot}", (r.x + 20, r.y + 12),
                      font_size=26, color=SERTAO_GOLD)
            draw_text(surface, f"Regiao: {info['biome']}", (r.x + 20, r.y + 44),
                      font_size=16, color=SERTAO_CREAM)
            draw_text(surface, f"Ouro: {info['gold']}", (r.x + 250, r.y + 44),
                      font_size=16, color=SERTAO_GOLD)
            draw_text(surface, f"Animais: {info['animals_count']}  Chefe: {info['bosses_defeated']}",
                      (r.x + 20, r.y + 64), font_size=15, color=SERTAO_CREAM)

            details = info.get("party_details") or []
            if details:
                names = ", ".join(m.get("name", "") for m in details[:3])
            else:
                names = "vazia"
            if len(names) > 38:
                names = names[:38] + "..."
            draw_text(surface, f"Equipe: {names}", (r.x + 20, r.y + 88),
                      font_size=13, color=SERTAO_LIGHT)

            if info.get("run_active"):
                run_color = SERTAO_GREEN
                run_txt = "Run ativa: SIM"
            else:
                run_color = SERTAO_RED
                run_txt = "Run ativa: NAO"
            draw_text(surface, run_txt, (r.x + 255, r.y + 110),
                      font_size=14, color=run_color)

            spr_x = r.x + 20
            for i, m in enumerate(details[:3]):
                spr = None
                if self.assets:
                    spr = self.assets.get_animal_sprite(
                        m["id"], evolution_stage=m.get("evolution_stage", 0),
                        max_width=40, max_height=40)
                if spr:
                    spr_rect = spr.get_rect(midleft=(spr_x, r.y + 124))
                    surface.blit(spr, spr_rect)
                    spr_x += spr.get_width() + 10
                else:
                    emoji = ANIMAL_EMOJIS.get(m.get("id", ""), "?")
                    draw_text(surface, emoji, (spr_x + 12, r.y + 124),
                              font_size=30, color=SERTAO_CREAM, center=True)
                    spr_x += 46

            sel_h = select_btn.collidepoint(get_mouse_pos())
            draw_sertao_button(surface, select_btn, "SELECIONAR", sel_h)
        else:
            draw_text(surface, f"SAVE {slot}", (r.x + 22, r.y + 12),
                      font_size=26, color=SERTAO_GOLD)
            draw_text(surface, "\U0001f512 VAZIO", (r.x + 22, r.y + 52),
                      font_size=22, color=GRAY)
            draw_text(surface, "Crie uma nova jornada neste slot",
                      (r.x + 22, r.y + 84), font_size=14, color=GRAY)
            nh = new_btn.collidepoint(get_mouse_pos())
            draw_sertao_button(surface, new_btn, "NOVA JORNADA", nh)


class SwapAnimalScreen:
    def __init__(self, party, new_animal_id, new_animal_name, assets=None):
        self.party = party
        self.new_animal_id = new_animal_id
        self.new_animal_name = new_animal_name
        self.assets = assets
        self.layout = UILayout()
        self.hover_index = -1
        self.cancel_hover = False
        self.slot_rects = []
        btn_w, btn_h = 380, 60
        start_y = self.layout.body.y + 100
        for i in range(3):
            x = CENTER_X - btn_w // 2
            y = start_y + i * (btn_h + 14)
            self.slot_rects.append(pygame.Rect(x, y, btn_w, btn_h))
        self.cancel_rect = pygame.Rect(CENTER_X - 100, start_y + 3 * (btn_h + 14), 200, 44)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            self.cancel_hover = False
            for i, r in enumerate(self.slot_rects):
                if i < len(self.party) and r.collidepoint(event.pos):
                    self.hover_index = i
                    break
            if self.cancel_rect.collidepoint(event.pos):
                self.cancel_hover = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.slot_rects):
                if i < len(self.party) and r.collidepoint(event.pos):
                    return ("swap", i)
            if self.cancel_rect.collidepoint(event.pos):
                return "cancel"
        return None

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        draw_text(surface, f"Equipe cheia! Substituir por {self.new_animal_name}?",
                  (CENTER_X, self.layout.header.center_y + 20),
                  font_size=28, color=SERTAO_GOLD, center=True)

        for i in range(3):
            if i < len(self.party):
                self._draw_slot(surface, self.party[i], i)

        is_h = self.cancel_rect.collidepoint(get_mouse_pos())
        draw_sertao_button(surface, self.cancel_rect, "Cancelar", is_h)

    def _draw_slot(self, surface, animal, index):
        r = self.slot_rects[index]
        is_h = self.hover_index == index
        border = SERTAO_GOLD if is_h else SERTAO_BORDER
        bg = (*SERTAO_PANEL, 220)

        panel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        panel.fill(bg)
        surface.blit(panel, r.topleft)
        pygame.draw.rect(surface, border, r, 2, border_radius=6)

        stage = getattr(animal, "evolution_stage", 0)
        stage_names = ["Base", "Evo 1"]
        if self.assets:
            spr = self.assets.get_animal_sprite(animal.animal_id,
                                               evolution_stage=stage,
                                               max_width=40, max_height=40)
            if spr:
                surface.blit(spr, spr.get_rect(center=(r.x + 25, r.centery)))
            else:
                emoji = ANIMAL_EMOJIS.get(animal.animal_id, "?")
                draw_text(surface, emoji, (r.x + 25, r.y + r.h // 2),
                          font_size=30, color=SERTAO_CREAM, center=True)
        else:
            emoji = ANIMAL_EMOJIS.get(animal.animal_id, "?")
            draw_text(surface, emoji, (r.x + 25, r.y + r.h // 2),
                      font_size=30, color=SERTAO_CREAM, center=True)
        form = stage_names[min(stage, 1)]
        draw_text(surface, f"{animal.name} [{form}]", (r.x + 55, r.y + 14),
                  font_size=20, color=SERTAO_CREAM)
        draw_text(surface, f"Nv {animal.level}", (r.x + 55, r.y + 38),
                  font_size=16, color=SERTAO_LIGHT)
