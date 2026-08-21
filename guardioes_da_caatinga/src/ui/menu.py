import pygame
from config import (WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN,
                    CREAM, ORANGE, PURPLE, SCREEN_WIDTH, SCREEN_HEIGHT,
                    DARK_BROWN, GOLD, load_animals, load_biomes, load_items,
                    load_enemies, load_upgrades)
from src.ui.layout import (UILayout, LayoutArea, draw_sertao_panel, draw_sertao_button,
                           draw_text, CENTER_X, CENTER_Y, SAFE_MARGIN,
                           SERTAO_DARK, SERTAO_PANEL, SERTAO_BORDER, SERTAO_LIGHT,
                           SERTAO_CREAM, SERTAO_GOLD, SERTAO_RED, SERTAO_GREEN)

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

ITEM_EMOJIS = {
    "casco_reforcado": "\U0001f6e1",
    "pegadas_rapidas": "\U0001f45f",
    "cantil_natural": "\U0001f4a7",
    "osso_resistente": "\U0001f9b4",
    "ervas_medicinais": "\U0001f33f",
    "medalha_do_sertao": "\U0001f525",
    "garra_afiada": "\u2694\ufe0f",
    "pena_sagrada": "\U0001fab6",
    "instinto_selvagem": "\U0001f43e",
    "couraca_natural": "\U0001f6e1",
    "olho_de_aguia": "\U0001f981",
}

RARITY_COLORS = {"Comum": GRAY, "Raro": BLUE, "\u00c9pico": PURPLE, "Lend\u00e1rio": SERTAO_GOLD}


def word_wrap(text, max_chars=40):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w) if cur else w
        if len(test) > max_chars:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


class MainMenu:
    def __init__(self, assets=None):
        self.assets = assets
        self.hover_index = -1
        self.layout = UILayout()
        self._build()

    def _build(self):
        labels = ["JOGAR", "BESTIARIO", "ACAMPAMENTO", "CONFIGURACOES", "SAVES", "SAIR"]
        btn_w, btn_h = 320, 52
        spacing = 12
        count = len(labels)
        total_h = count * btn_h + (count - 1) * spacing
        start_y = self.layout.body.center_y - total_h // 2 + 20

        self.buttons = []
        for i, label in enumerate(labels):
            x = CENTER_X - btn_w // 2
            y = start_y + i * (btn_h + spacing)
            self.buttons.append({"rect": pygame.Rect(x, y, btn_w, btn_h), "label": label})

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, b in enumerate(self.buttons):
                if b["rect"].collidepoint(event.pos):
                    self.hover_index = i
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, b in enumerate(self.buttons):
                if b["rect"].collidepoint(event.pos):
                    return i
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
                               is_hovered=(self.hover_index == i))

        fv = pygame.font.Font(None, 18)
        vs = fv.render("Versao 1.0", True, GRAY)
        surface.blit(vs, vs.get_rect(center=(CENTER_X, self.layout.footer.center_y)))


class AnimalSelectScreen:
    def __init__(self, unlocked_animals=None, assets=None, save_data=None):
        self.animals = load_animals()
        self.unlocked_animals = unlocked_animals or ["tatu_bola"]
        self.save_data = save_data or {}
        self.assets = assets
        self.hover_index = -1
        self.layout = UILayout()
        self._build_cards()

    def _build_cards(self):
        self.cards = []
        animal_ids = list(self.animals.keys())
        card_w, card_h = 500, 78
        spacing = 8
        count = len(animal_ids)
        total_h = count * card_h + (count - 1) * spacing
        start_y = self.layout.body.y + (self.layout.body.h - total_h) // 2

        for i, aid in enumerate(animal_ids):
            x = CENTER_X - card_w // 2
            y = start_y + i * (card_h + spacing)
            self.cards.append({
                "id": aid,
                "animal": self.animals[aid],
                "rect": pygame.Rect(x, y, card_w, card_h),
                "unlocked": aid in self.unlocked_animals,
                "level": self.save_data.get("animal_data", {}).get(aid, {}).get("level", 1),
            })

        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            for i, c in enumerate(self.cards):
                if c["rect"].collidepoint(event.pos) and c["unlocked"]:
                    self.hover_index = i
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for c in self.cards:
                if c["rect"].collidepoint(event.pos) and c["unlocked"]:
                    return c["id"]
            if self.back_button.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "animal_select")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "Escolha seu Animal", (CENTER_X, 40),
                  font_size=44, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Cada animal possui caracteristicas unicas.",
                  (CENTER_X, 80), font_size=22, color=SERTAO_CREAM, center=True)
        pygame.draw.line(surface, SERTAO_BORDER, (CENTER_X - 200, 108), (CENTER_X + 200, 108), 2)

        for i, card in enumerate(self.cards):
            self._draw_card(surface, card, i)

        bh = self.back_button.collidepoint(pygame.mouse.get_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)

    def _draw_card(self, surface, card, index):
        r = card["rect"]
        animal = card["animal"]
        hov = (self.hover_index == index)

        draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                          SERTAO_GOLD if hov and card["unlocked"] else SERTAO_BORDER)

        if self.assets and card["unlocked"]:
            spr = self.assets.get_animal_sprite(card["id"], max_width=50, max_height=50)
            if spr:
                surface.blit(spr, spr.get_rect(midleft=(r.x + 10, r.centery)))
            else:
                emoji = ANIMAL_EMOJIS.get(card["id"], "?")
                draw_text(surface, emoji, (r.x + 20, r.y + 14), font_size=30)

        tx = r.x + 75
        if card["unlocked"]:
            draw_text(surface, animal["name"], (tx, r.y + 6), font_size=22, color=SERTAO_CREAM)
            draw_text(surface, f"Nv.{card['level']}", (tx + 200, r.y + 8),
                      font_size=18, color=SERTAO_GOLD)
            draw_text(surface, animal["role"], (tx + 260, r.y + 8), font_size=16, color=SERTAO_LIGHT)
            s = animal["base_stats"]
            draw_text(surface, f"HP:{s['hp']}  ATK:{s['attack']}  DEF:{s['defense']}  SPD:{s['speed']}",
                      (tx, r.y + 30), font_size=14, color=SERTAO_CREAM)
            diff = "Facil" if s["hp"] >= 70 else ("Medio" if s["speed"] >= 10 else "Dificil")
            dc = GREEN if diff == "Facil" else (YELLOW if diff == "Medio" else RED)
            draw_text(surface, f"Dificuldade: {diff}", (tx, r.y + 50), font_size=14, color=dc)
        else:
            draw_text(surface, animal["name"], (tx, r.y + 10), font_size=22, color=GRAY)
            draw_text(surface, "Bloqueado", (tx, r.y + 38), font_size=20, color=RED)


class BestiaryScreen:
    def __init__(self, save_data=None, assets=None):
        self.animals = load_animals()
        self.enemies = load_enemies()
        self.save_data = save_data or {}
        self.assets = assets
        self.unlocked_animals = self.save_data.get("unlocked_animals", [])
        self.bestiary_discovered = self.save_data.get("bestiary_discovered", [])
        self.creatures_discovered = self.save_data.get("creatures_discovered", [])
        self.tab = "ANIMAIS"
        self.selected_idx = 0
        self.hover_idx = -1
        self.layout = UILayout()
        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)
        self.tab_animals = pygame.Rect(CENTER_X - 260, 75, 240, 36)
        self.tab_criaturas = pygame.Rect(CENTER_X + 20, 75, 240, 36)
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
        start_y = self.layout.body.y + 90
        grid_w = cols * cell_w + (cols - 1) * gap_x
        actual_start_x = CENTER_X - grid_w // 2

        for i, eid in enumerate(ids):
            row = i // cols
            col = i % cols
            x = actual_start_x + col * (cell_w + gap_x)
            y = start_y + row * (cell_h + gap_y)
            discovered = eid in (self.bestiary_discovered if self.tab == "ANIMAIS" else self.creatures_discovered)
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
                           color=SERTAO_GREEN if is_animals else SERTAO_PANEL)
        draw_sertao_button(surface, self.tab_criaturas, "CRIATURAS", is_hovered=not is_animals,
                           color=SERTAO_RED if not is_animals else SERTAO_PANEL)

        discovered_list = self.bestiary_discovered if is_animals else self.creatures_discovered
        total_ids = self._get_current_ids()
        total = len(total_ids)
        discovered = len([e for e in discovered_list if e in total_ids])
        pct = int((discovered / total) * 100) if total > 0 else 0

        draw_text(surface, f"Descobertas: {discovered} / {total}  ({pct}%)",
                  (CENTER_X, 120), font_size=18, color=SERTAO_CREAM, center=True)

        bar_w = 360
        bar_h = 8
        bar_x = CENTER_X - bar_w // 2
        bar_y = 142
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
        detail_y = self.layout.body.y + 90
        detail_h = SCREEN_HEIGHT - detail_y - 80

        if detail_w > 100:
            self._draw_detail_panel(surface, detail_x, detail_y, detail_w, detail_h)

        bh = self.back_button.collidepoint(pygame.mouse.get_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)

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

        if self.tab == "ANIMAIS":
            animal = self.animals.get(cell["id"], {})
            if discovered:
                if self.assets and cell.get("unlocked"):
                    spr = self.assets.get_animal_sprite(cell["id"], max_width=38, max_height=38)
                    if spr:
                        surface.blit(spr, spr.get_rect(center=(r.x + 25, r.y + 25)))
                    else:
                        emoji = ANIMAL_EMOJIS.get(cell["id"], "?")
                        draw_text(surface, emoji, (r.x + 10, r.y + 8), font_size=24)
                elif discovered:
                    emoji = ANIMAL_EMOJIS.get(cell["id"], "?")
                    draw_text(surface, emoji, (r.x + 10, r.y + 8), font_size=24, color=GRAY)

                name = animal.get("name", cell["id"])
                draw_text(surface, name, (r.x + 55, r.y + 8), font_size=18, color=SERTAO_CREAM)
                draw_text(surface, animal.get("role", ""), (r.x + 55, r.y + 30),
                          font_size=14, color=SERTAO_LIGHT)
                rarity = animal.get("rarity", "")
                rc = RARITY_COLORS.get(rarity, GRAY)
                draw_text(surface, rarity, (r.x + 55, r.y + 50), font_size=13, color=rc)

                if cell.get("unlocked"):
                    draw_text(surface, "\u2713", (r.right - 18, r.y + 8), font_size=18, color=GREEN)
            else:
                draw_text(surface, "\U0001f512", (r.x + 10, r.y + 8), font_size=24, color=(60, 50, 40))
                draw_text(surface, "???", (r.x + 50, r.y + 15), font_size=20, color=(60, 50, 40))
        else:
            enemy_data = self.enemies.get(cell["id"], {})
            emoji = ENEMY_EMOJIS.get(cell["id"], "\U0001f525")
            if discovered:
                if self.assets:
                    spr = self.assets.get_enemy_sprite(cell["id"], max_width=38, max_height=38)
                    if spr:
                        surface.blit(spr, spr.get_rect(center=(r.x + 25, r.y + 25)))
                    else:
                        draw_text(surface, emoji, (r.x + 10, r.y + 8), font_size=24)
                else:
                    draw_text(surface, emoji, (r.x + 10, r.y + 8), font_size=24)

                name = enemy_data.get("name", cell["id"])
                draw_text(surface, name, (r.x + 55, r.y + 8), font_size=18, color=SERTAO_CREAM)

                is_boss = enemy_data.get("is_boss", False)
                is_elite = enemy_data.get("is_elite", False)
                tag = "CHEFE" if is_boss else ("ELITE" if is_elite else "Comum")
                tag_color = SERTAO_RED if is_boss else (ORANGE if is_elite else GRAY)
                draw_text(surface, tag, (r.x + 55, r.y + 30), font_size=13, color=tag_color)

                region = enemy_data.get("region", "")
                draw_text(surface, region, (r.x + 55, r.y + 48), font_size=13, color=SERTAO_LIGHT)
            else:
                draw_text(surface, "\U0001f512", (r.x + 10, r.y + 8), font_size=24, color=(60, 50, 40))
                draw_text(surface, "???", (r.x + 50, r.y + 15), font_size=20, color=(60, 50, 40))

    def _draw_detail_panel(self, surface, x, y, w, h):
        draw_sertao_panel(surface, x, y, w, h)
        selected_id = self._get_selected()
        px = x + 15
        py = y + 15

        if self.tab == "ANIMAIS":
            animal = self.animals.get(selected_id, {})
            discovered = selected_id in self.bestiary_discovered
            unlocked = selected_id in self.unlocked_animals

            if discovered:
                if self.assets and unlocked:
                    spr = self.assets.get_animal_sprite(selected_id, max_width=55, max_height=55)
                    if spr:
                        surface.blit(spr, spr.get_rect(topleft=(px, py)))
                    else:
                        icon_rect = pygame.Rect(px, py, 55, 55)
                        pygame.draw.rect(surface, SERTAO_GREEN, icon_rect, border_radius=10)
                else:
                    icon_rect = pygame.Rect(px, py, 55, 55)
                    pygame.draw.rect(surface, SERTAO_GREEN if unlocked else GRAY, icon_rect, border_radius=10)

                draw_text(surface, animal.get("name", ""), (px + 65, py + 5),
                          font_size=22, color=SERTAO_CREAM)
                draw_text(surface, animal.get("role", ""), (px + 65, py + 30),
                          font_size=16, color=SERTAO_LIGHT)
                rarity = animal.get("rarity", "")
                rc = RARITY_COLORS.get(rarity, GRAY)
                draw_text(surface, rarity, (px + 65, py + 50), font_size=14, color=rc)

                py += 70
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

                desc_lines = word_wrap(animal.get("description", ""), max_chars=32)
                for line in desc_lines[:3]:
                    draw_text(surface, line, (px, py), font_size=14, color=SERTAO_CREAM)
                    py += 18

                py += 5
                pygame.draw.line(surface, SERTAO_BORDER, (px, py), (x + w - 15, py), 1)
                py += 8

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
                rescue_lines = word_wrap(rescue, max_chars=32)
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
                desc_lines = word_wrap(desc, max_chars=32)
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
    SECTIONS = ["EQUIPAMENTOS", "MELHORIAS", "ITENS", "EQUIPE"]

    def __init__(self, save_data=None, assets=None, party=None):
        self.save_data = save_data or {}
        self.assets = assets
        self.party = party or []
        self.animals = load_animals()
        self.items = load_items()
        self.upgrades_data = load_upgrades()
        self.unlocked = self.save_data.get("unlocked_animals", [])
        self.sel_section = 0
        self.sel_item = -1
        self.sel_animal = 0
        self.hover_item = -1
        self.equip_mode = False
        self.equip_hover = -1
        self.layout = UILayout()
        self._build_tabs()

    def _build_tabs(self):
        tab_w, tab_h = 145, 34
        spacing = 8
        count = len(self.SECTIONS)
        total = count * tab_w + (count - 1) * spacing
        start_x = CENTER_X - total // 2
        self.tab_rects = []
        for i, name in enumerate(self.SECTIONS):
            x = start_x + i * (tab_w + spacing)
            self.tab_rects.append(pygame.Rect(x, 75, tab_w, tab_h))
        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, tab in enumerate(self.tab_rects):
                if tab.collidepoint(event.pos):
                    self.sel_section = i
                    self.sel_item = -1
                    self.equip_mode = False
                    return None

            if self.back_button.collidepoint(event.pos):
                return ("back", None)

            if self.sel_section == 0:
                return self._handle_equip_events(event)
            elif self.sel_section == 1:
                return self._handle_melhorias_events(event)
            elif self.sel_section == 2:
                return self._handle_itens_events(event)
            elif self.sel_section == 3:
                return self._handle_equipe_events(event)

        if event.type == pygame.MOUSEMOTION:
            self.hover_item = -1
            self.equip_hover = -1
            if self.sel_section == 0 and self.equip_mode:
                inv = self.save_data.get("inventory", [])
                rects = self._get_item_rects()
                for i in range(len(inv)):
                    if i < len(rects) and rects[i].collidepoint(event.pos):
                        self.equip_hover = i
                        break

        return None

    def _handle_equip_events(self, event):
        if self.equip_mode:
            inv = self.save_data.get("inventory", [])
            rects = self._get_item_rects()
            for i in range(len(inv)):
                if i < len(rects) and rects[i].collidepoint(event.pos):
                    return ("equip", i)
            cancel = pygame.Rect(CENTER_X - 100, SCREEN_HEIGHT - 120, 200, 38)
            if cancel.collidepoint(event.pos):
                self.equip_mode = False
            return None

        btn_equip = pygame.Rect(SAFE_MARGIN + 30, SCREEN_HEIGHT - 120, 200, 38)
        btn_unequip = pygame.Rect(SAFE_MARGIN + 250, SCREEN_HEIGHT - 120, 200, 38)
        if btn_equip.collidepoint(event.pos):
            self.equip_mode = True
            return None
        if btn_unequip.collidepoint(event.pos):
            return ("unequip", None)
        return None

    def _handle_melhorias_events(self, event):
        return None

    def _handle_itens_events(self, event):
        inv = self.save_data.get("inventory", [])
        rects = self._get_item_rects()
        for i in range(len(inv)):
            if i < len(rects) and rects[i].collidepoint(event.pos):
                self.sel_item = i
        return None

    def _handle_equipe_events(self, event):
        rects = self._get_party_rects()
        for i in range(len(self.party)):
            if i < len(rects) and rects[i].collidepoint(event.pos):
                self.sel_animal = i
        return None

    def _get_item_rects(self):
        bw, bh = 500, 48
        gap = 8
        inv = self.save_data.get("inventory", [])
        total = len(inv) * bh + max(0, len(inv) - 1) * gap
        sy = 170
        rects = []
        for i in range(len(inv)):
            x = CENTER_X - bw // 2
            y = sy + i * (bh + gap)
            rects.append(pygame.Rect(x, y, bw, bh))
        return rects

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
                               color=SERTAO_GREEN if is_sel else SERTAO_PANEL)

        if self.sel_section == 0:
            self._draw_equip_section(surface)
        elif self.sel_section == 1:
            self._draw_melhorias_section(surface)
        elif self.sel_section == 2:
            self._draw_itens_section(surface)
        elif self.sel_section == 3:
            self._draw_equipe_section(surface)

        bh = self.back_button.collidepoint(pygame.mouse.get_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)

    def _draw_equip_section(self, surface):
        draw_text(surface, "Equipar itens nos animais desbloqueados",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        if self.equip_mode:
            inv = self.save_data.get("inventory", [])
            rects = self._get_item_rects()
            draw_text(surface, "Selecione um item para equipar:", (CENTER_X, 145),
                      font_size=16, color=SERTAO_GOLD, center=True)
            for i, iid in enumerate(inv):
                if i >= len(rects):
                    break
                r = rects[i]
                item = self.items.get(iid, {})
                is_hov = (self.equip_hover == i)
                draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                                  SERTAO_GOLD if is_hov else SERTAO_BORDER)
                emoji = ITEM_EMOJIS.get(iid, "\U0001f392")
                draw_text(surface, f"{emoji} {item.get('name', iid)}", (r.x + 15, r.y + 10),
                          font_size=18, color=SERTAO_CREAM)
                draw_text(surface, item.get("description", ""), (r.x + 15, r.y + 30),
                          font_size=13, color=SERTAO_LIGHT)

            cancel = pygame.Rect(CENTER_X - 100, SCREEN_HEIGHT - 120, 200, 38)
            draw_sertao_button(surface, cancel, "Cancelar", False)
            return

        inv = self.save_data.get("inventory", [])
        if not inv:
            draw_text(surface, "Nenhum item no inventario.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
        else:
            rects = self._get_item_rects()
            for i, iid in enumerate(inv):
                if i >= len(rects):
                    break
                r = rects[i]
                item = self.items.get(iid, {})
                draw_sertao_panel(surface, r.x, r.y, r.w, r.h)
                emoji = ITEM_EMOJIS.get(iid, "\U0001f392")
                draw_text(surface, f"{emoji} {item.get('name', iid)}", (r.x + 15, r.y + 8),
                          font_size=18, color=SERTAO_CREAM)
                draw_text(surface, item.get("description", ""), (r.x + 15, r.y + 28),
                          font_size=13, color=SERTAO_LIGHT)

            btn_equip = pygame.Rect(SAFE_MARGIN + 30, SCREEN_HEIGHT - 120, 200, 38)
            btn_unequip = pygame.Rect(SAFE_MARGIN + 250, SCREEN_HEIGHT - 120, 200, 38)
            draw_sertao_button(surface, btn_equip, "Equipar Item", False)
            draw_sertao_button(surface, btn_unequip, "Desequipar", False)

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

    def _draw_itens_section(self, surface):
        draw_text(surface, "Itens coletados",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        inv = self.save_data.get("inventory", [])
        if not inv:
            draw_text(surface, "Nenhum item coletado ainda.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
            return

        rects = self._get_item_rects()
        for i, iid in enumerate(inv):
            if i >= len(rects):
                break
            r = rects[i]
            item = self.items.get(iid, {})
            is_hov = (self.hover_item == i)
            draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                              SERTAO_GOLD if is_hov else SERTAO_BORDER)
            emoji = ITEM_EMOJIS.get(iid, "\U0001f392")
            draw_text(surface, f"{emoji} {item.get('name', iid)}", (r.x + 15, r.y + 8),
                      font_size=18, color=SERTAO_CREAM)
            draw_text(surface, item.get("description", ""), (r.x + 15, r.y + 28),
                      font_size=13, color=SERTAO_LIGHT)

            rarity = item.get("rarity", "common")
            rarity_map = {"common": GRAY, "uncommon": BLUE, "rare": PURPLE}
            rc = rarity_map.get(rarity, GRAY)
            draw_text(surface, rarity.capitalize(), (r.right - 15, r.y + 10),
                      font_size=13, color=rc, center=False)

    def _draw_equipe_section(self, surface):
        draw_text(surface, "Equipe atual (max 3)",
                  (CENTER_X, 155), font_size=16, color=SERTAO_CREAM, center=True)

        if not self.party:
            draw_text(surface, "Nenhum animal na equipe.", (CENTER_X, 300),
                      font_size=20, color=GRAY, center=True)
            return

        rects = self._get_party_rects()
        for i, member in enumerate(self.party):
            if i >= len(rects):
                break
            r = rects[i]
            is_hov = (self.hover_item == i)
            draw_sertao_panel(surface, r.x, r.y, r.w, r.h,
                              SERTAO_GOLD if is_hov else SERTAO_BORDER)

            if self.assets:
                spr = self.assets.get_animal_sprite(member.animal_id, max_width=44, max_height=44)
                if spr:
                    surface.blit(spr, spr.get_rect(center=(r.x + 30, r.centery)))
                else:
                    emoji = ANIMAL_EMOJIS.get(member.animal_id, "?")
                    draw_text(surface, emoji, (r.x + 12, r.y + 8), font_size=28)
            else:
                emoji = ANIMAL_EMOJIS.get(member.animal_id, "?")
                draw_text(surface, emoji, (r.x + 12, r.y + 8), font_size=28)

            draw_text(surface, member.name, (r.x + 65, r.y + 8), font_size=20, color=SERTAO_CREAM)
            draw_text(surface, member.role, (r.x + 65, r.y + 30), font_size=14, color=SERTAO_LIGHT)
            draw_text(surface, f"Lv.{member.level}  HP:{member.hp}/{member.max_hp}",
                      (r.x + 65, r.y + 45), font_size=13, color=SERTAO_GOLD)

            if member.equipped_item:
                items_data = load_items()
                item_info = items_data.get(member.equipped_item, {})
                item_name = item_info.get("name", member.equipped_item)
                draw_text(surface, f"Eq: {item_name}", (r.x + 280, r.y + 8),
                          font_size=13, color=SERTAO_GOLD)
            else:
                draw_text(surface, "Sem item", (r.x + 280, r.y + 8),
                          font_size=13, color=GRAY)

            s = member
            draw_text(surface, f"ATK:{s.attack} DEF:{s.defense} SPD:{s.speed}",
                      (r.right - 15, r.y + 12), font_size=13, color=SERTAO_CREAM, center=False)


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

        bh = self.back_button.collidepoint(pygame.mouse.get_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)


class SettingsScreen:
    def __init__(self, assets=None):
        self.assets = assets
        self.layout = UILayout()
        self.back_button = self.layout.center_column(300, 50, count=1)[0]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                return True
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "settings")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "Configuracoes", (CENTER_X, 80),
                  font_size=44, color=SERTAO_GOLD, center=True)
        draw_text(surface, "Em desenvolvimento...", (CENTER_X, 200),
                  font_size=28, color=GRAY, center=True)

        bh = self.back_button.collidepoint(pygame.mouse.get_pos())
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


class SaveScreen:
    def __init__(self, save_manager, assets=None):
        self.save_manager = save_manager
        self.assets = assets
        self.layout = UILayout()
        self.hover_slot = -1
        self.confirm_delete = None
        self.info_cache = {}
        self._refresh()

    def _refresh(self):
        self.info_cache = {}
        for s in range(1, 4):
            self.info_cache[s] = self.save_manager.get_slot_info(s)
        self.slot_rects = []
        btn_w, btn_h = 460, 120
        spacing = 16
        start_y = self.layout.body.y + 40
        for i in range(3):
            x = CENTER_X - btn_w // 2
            y = start_y + i * (btn_h + spacing)
            self.slot_rects.append(pygame.Rect(x, y, btn_w, btn_h))
        self.back_button = pygame.Rect(SAFE_MARGIN, SCREEN_HEIGHT - 65, 140, 42)
        self.confirm_rects = {
            "delete": pygame.Rect(CENTER_X - 160, SCREEN_HEIGHT // 2 + 60, 140, 38),
            "cancel": pygame.Rect(CENTER_X + 20, SCREEN_HEIGHT // 2 + 60, 140, 38),
        }

    def handle_event(self, event):
        if self.confirm_delete is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.confirm_rects["delete"].collidepoint(event.pos):
                    self.save_manager.delete_save(self.confirm_delete)
                    self.confirm_delete = None
                    self._refresh()
                    return None
                elif self.confirm_rects["cancel"].collidepoint(event.pos):
                    self.confirm_delete = None
                    return None
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
                if r.collidepoint(event.pos):
                    slot = i + 1
                    if self.info_cache.get(slot):
                        return ("load", slot)
                    else:
                        return ("new", slot)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i in range(3):
                    slot = i + 1
                    if self.info_cache.get(slot):
                        r = self.slot_rects[i]
                        del_x = r.right - 30
                        del_y = r.y + 10
                        if abs(mx - del_x) < 15 and abs(my - del_y) < 15:
                            self.confirm_delete = slot
                            return None
        return None

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "main_menu")
        else:
            surface.fill(SERTAO_DARK)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "Saves", (CENTER_X, self.layout.header.center_y),
                  font_size=40, color=SERTAO_GOLD, center=True)

        for i in range(3):
            slot = i + 1
            info = self.info_cache.get(slot)
            self._draw_slot(surface, slot, info, i)

        if self.confirm_delete is not None:
            self._draw_confirm(surface)

        bh = self.back_button.collidepoint(pygame.mouse.get_pos())
        draw_sertao_button(surface, self.back_button, "Voltar", bh)

    def _draw_slot(self, surface, slot, info, index):
        r = self.slot_rects[index]
        is_hover = self.hover_slot == index

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

        draw_text(surface, f"SAVE {slot}", (r.x + 20, r.y + 12),
                  font_size=26, color=SERTAO_GOLD)

        if info:
            draw_text(surface, f"Animais: {info['animals_count']}/{info['animals_total']}",
                      (r.x + 20, r.y + 44), font_size=18, color=SERTAO_CREAM)
            draw_text(surface, f"Regioes: {info['biomes_count']}/{info['biomes_total']}",
                      (r.x + 20, r.y + 66), font_size=18, color=SERTAO_CREAM)
            draw_text(surface, f"Tempo: {info['play_time']}",
                      (r.x + 250, r.y + 44), font_size=18, color=SERTAO_CREAM)
            if info['last_animal']:
                draw_text(surface, f"Ultimo: {info['last_animal']}",
                          (r.x + 250, r.y + 66), font_size=18, color=SERTAO_CREAM)

            del_label = "X"
            del_color = SERTAO_RED
            draw_text(surface, del_label, (r.right - 22, r.y + 14),
                      font_size=20, color=del_color)
        else:
            draw_text(surface, "Vazio — Clique para criar", (r.x + 20, r.y + 50),
                      font_size=20, color=GRAY)

    def _draw_confirm(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pw, ph = 400, 160
        pr = pygame.Rect(CENTER_X - pw // 2, SCREEN_HEIGHT // 2 - ph // 2, pw, ph)
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*SERTAO_PANEL, 240))
        surface.blit(panel, pr.topleft)
        pygame.draw.rect(surface, SERTAO_BORDER, pr, 2, border_radius=8)

        draw_text(surface, f"Apagar SAVE {self.confirm_delete}?",
                  (CENTER_X, pr.y + 30), font_size=24, color=SERTAO_RED, center=True)
        draw_text(surface, "Essa acao e irreversivel.",
                  (CENTER_X, pr.y + 60), font_size=18, color=GRAY, center=True)

        for key, rect in self.confirm_rects.items():
            is_h = rect.collidepoint(pygame.mouse.get_pos())
            label = "Apagar" if key == "delete" else "Cancelar"
            color = SERTAO_RED if key == "delete" else SERTAO_CREAM
            draw_sertao_button(surface, rect, label, is_h)


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

        is_h = self.cancel_rect.collidepoint(pygame.mouse.get_pos())
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

        emoji = ANIMAL_EMOJIS.get(animal.animal_id, "?")
        draw_text(surface, emoji, (r.x + 25, r.y + r.h // 2),
                  font_size=30, color=SERTAO_CREAM, center=True)
        draw_text(surface, animal.name, (r.x + 55, r.y + 14),
                  font_size=22, color=SERTAO_CREAM)
        draw_text(surface, f"Nv {animal.level}", (r.x + 55, r.y + 38),
                  font_size=16, color=SERTAO_LIGHT)
