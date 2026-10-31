import pygame
import time
from config import (WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN,
                    CREAM, SCREEN_WIDTH, SCREEN_HEIGHT, NODE_COLORS, BIOME_COLORS)
from src.ui.components import draw_text
from src.ui.layout import SERTAO_GOLD, draw_sertao_button
from src.ui.text import get_font, draw_text_block_colored, measure_block
from src.state import NodeType

NODE_TOOLTIPS = {
    NodeType.COMBAT: {
        "title": "Batalha Normal",
        "lines": [
            "Inimigos do bioma atual.",
            "Ganha 1 nivel ao vencer.",
            "Chance de encontrar reliquias."
        ]
    },
    NodeType.ELITE: {
        "title": "Batalha Elite",
        "lines": [
            "Inimigos MUITO mais fortes.",
            "Combatentes extras na batalha.",
            "Recompensa muito maior:",
            "mais XP e muito mais ouro."
        ]
    },
    NodeType.EVENT: {
        "title": "Evento",
        "lines": [
            "Escolhas especiais.",
            "Possiveis recompensas",
            "ou penalidades."
        ]
    },
    NodeType.CAMP: {
        "title": "Acampamento",
        "lines": [
            "Recupere 30% da vida.",
            "Ponto seguro no sertao."
        ]
    },
    NodeType.SHOP: {
        "title": "Loja",
        "lines": [
            "Compre melhorias.",
            "Compre reliquias.",
            "Gaste seu gold."
        ]
    },
    NodeType.BOSS: {
        "title": "Chefe da Regiao",
        "lines": [
            "Inimigo poderoso!",
            "Libera um novo animal.",
            "Grande recompensa."
        ]
    },
    NodeType.RESCUE_ANIMAL: {
        "title": "Encontro Animal",
        "lines": [
            "Um animal precisa de ajuda.",
            "Possibilidade de recrutar",
            "um novo membro para equipe."
        ]
    }
}


class MapUI:
    NODE_ICON_HEIGHT = 52
    BUTTON_ORDER = ("inicio", "bestiario", "inventario", "missoes")
    BUTTON_LABELS = {
        "inicio": "INICIO",
        "bestiario": "BESTIARIO",
        "inventario": "INVENTARIO",
        "missoes": "MISSOES",
    }
    BUTTON_WIDTH = 190
    BUTTON_X = 30
    BUTTON_START_Y = 248
    BUTTON_GAP = 12

    def __init__(self, map_generator, biome_id, assets=None):
        self.map_gen = map_generator
        self.biome_id = biome_id
        self.assets = assets
        self.node_radius = 26
        self.node_positions = {}
        self.calculate_positions()

        self.hover_start_time = None
        self.hovered_node_id = None
        self.tooltip_alpha = 0
        self.tooltip_max_alpha = 220
        self.tooltip_fade_speed = 8

        self._node_icon_cache = {}
        self._available_glow = self._make_glow((255, 210, 80, 26),
                                               self.node_radius + 10)
        self._available_ring = self._make_ring((255, 215, 0, 70),
                                               self.node_radius + 8, 2)
        self._hover_ring = self._make_ring((255, 230, 80, 210),
                                           self.node_radius + 8, 3)

        self.hovered_button = None
        self.button_rects = {}
        self._button_cache = {}
        self._build_buttons()

    def _build_buttons(self):
        self.button_rects = {}
        y = self.BUTTON_START_Y
        for key in self.BUTTON_ORDER:
            surface = None
            if self.assets:
                surface = self.assets.get_ui_button(key, self.BUTTON_WIDTH)
            height = surface.get_height() if surface else 78
            self.button_rects[key] = pygame.Rect(
                self.BUTTON_X, y, self.BUTTON_WIDTH, height)
            y += height + self.BUTTON_GAP

    def calculate_positions(self):
        floors = {}
        for node_id, node in self.map_gen.nodes.items():
            if node.floor not in floors:
                floors[node.floor] = []
            floors[node.floor].append(node)

        available_height = SCREEN_HEIGHT - 180
        floor_height = available_height / max(len(floors) - 1, 1)

        for floor, nodes in floors.items():
            nodes.sort(key=lambda n: n.position)
            y = 80 + floor * floor_height
            spacing = min(180, (SCREEN_WIDTH - 200) / max(len(nodes) - 1, 1))
            start_x = (SCREEN_WIDTH - (len(nodes) - 1) * spacing) / 2

            for i, node in enumerate(nodes):
                x = start_x + i * spacing
                self.node_positions[node.node_id] = (int(x), int(y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._handle_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for key, rect in self.button_rects.items():
                if rect.collidepoint(event.pos):
                    return ("action", key)
            for node_id, pos in self.node_positions.items():
                node = self.map_gen.nodes.get(node_id)
                if node and node.available and not node.blocked:
                    dist = ((event.pos[0] - pos[0]) ** 2 + (event.pos[1] - pos[1]) ** 2) ** 0.5
                    if dist <= self.node_radius + 5:
                        self.hover_start_time = None
                        self.hovered_node_id = None
                        self.tooltip_alpha = 0
                        return ("node", node_id)
        return None

    def _handle_hover(self, mouse_pos):
        hovered_button = None
        for key, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                hovered_button = key
                break

        self.hovered_button = hovered_button
        if hovered_button:
            if self.hovered_node_id is not None:
                self.hovered_node_id = None
                self.hover_start_time = None
                self.tooltip_alpha = 0
            return

        found_node = None
        for node_id, pos in self.node_positions.items():
            node = self.map_gen.nodes.get(node_id)
            if node and not node.blocked:
                dist = ((mouse_pos[0] - pos[0]) ** 2 + (mouse_pos[1] - pos[1]) ** 2) ** 0.5
                if dist <= self.node_radius + 5:
                    found_node = node_id
                    break

        if found_node != self.hovered_node_id:
            self.hovered_node_id = found_node
            self.hover_start_time = time.time() if found_node else None
            self.tooltip_alpha = 0

        if self.hovered_node_id is not None and self.hover_start_time:
            elapsed = time.time() - self.hover_start_time
            if elapsed >= 1.0:
                self.tooltip_alpha = min(self.tooltip_max_alpha, self.tooltip_alpha + self.tooltip_fade_speed)
            else:
                self.tooltip_alpha = 0
        else:
            self.tooltip_alpha = 0

    def draw(self, surface):
        if self.assets:
            self.assets.draw_background(surface, "map")
        else:
            biome_color = BIOME_COLORS.get(self.biome_id, (50, 50, 50))
            surface.fill(biome_color)
            for x in range(0, SCREEN_WIDTH, 60):
                for y in range(0, SCREEN_HEIGHT, 60):
                    c = tuple(max(0, v - 15) for v in biome_color)
                    pygame.draw.circle(surface, c, (x, y), 1)

        biome_name = self.biome_id.replace('_', ' ').title()
        draw_text(surface, f"Regiao: {biome_name}", (270, 118),
                  font_size=18, color=(95, 60, 25))

        for node_id, node in self.map_gen.nodes.items():
            if node_id in self.node_positions:
                self._draw_connections(surface, node)

        for node_id, node in self.map_gen.nodes.items():
            if node_id in self.node_positions:
                self._draw_node(surface, node)

        self._draw_legend(surface)
        self._draw_buttons(surface)
        self._draw_tooltip(surface)

    def _draw_connections(self, surface, node):
        start_pos = self.node_positions.get(node.node_id)
        if not start_pos:
            return
        for conn_id in node.connections:
            end_pos = self.node_positions.get(conn_id)
            if end_pos:
                conn_node = self.map_gen.nodes.get(conn_id)
                if node.blocked or (conn_node and conn_node.blocked):
                    color = (30, 30, 30)
                elif node.visited:
                    color = GRAY
                else:
                    color = DARK_GRAY
                pygame.draw.line(surface, color, start_pos, end_pos, 2)

    @staticmethod
    def _make_glow(color, radius):
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (radius, radius), radius)
        return surface

    @staticmethod
    def _make_ring(color, radius, width):
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (radius, radius), radius, width)
        return surface

    def _get_node_icon_surface(self, node):
        mode = "normal"
        if node.blocked:
            mode = "blocked"
        elif node.visited:
            mode = "visited"
        elif not node.available:
            mode = "dim"

        cache_key = (node.node_type.value, mode)
        if cache_key in self._node_icon_cache:
            return self._node_icon_cache[cache_key]

        icon = None
        if self.assets:
            icon = self.assets.get_node_icon(
                node.node_type, self.NODE_ICON_HEIGHT)
        if icon is not None and mode != "normal":
            icon = icon.copy()
            if mode == "visited":
                tint = (150, 150, 150, 255)
            elif mode == "dim":
                tint = (200, 200, 200, 255)
            else:  # blocked
                tint = (85, 85, 85, 255)
            icon.fill(tint, special_flags=pygame.BLEND_RGBA_MULT)

        self._node_icon_cache[cache_key] = icon
        return icon

    def _draw_node(self, surface, node):
        pos = self.node_positions.get(node.node_id)
        if not pos:
            return

        icon = self._get_node_icon_surface(node)
        if icon is None:
            self._draw_node_fallback(surface, node, pos)
            return

        available = node.available and not node.blocked
        if available:
            surface.blit(self._available_glow,
                         self._available_glow.get_rect(center=pos))
            surface.blit(self._available_ring,
                         self._available_ring.get_rect(center=pos))

        if available and self.hovered_node_id == node.node_id:
            surface.blit(self._hover_ring,
                         self._hover_ring.get_rect(center=pos))

        surface.blit(icon, icon.get_rect(center=pos))

        if node.visited:
            check = get_font(18).render("\u2713", True, GREEN)
            surface.blit(check, (pos[0] + 16, pos[1] - 26))

    def _draw_node_fallback(self, surface, node, pos):
        """Old circle + letter rendering, used when the icon art is missing."""
        if node.blocked:
            color = (30, 30, 30)
        else:
            color = NODE_COLORS.get(node.node_type.value, GRAY)
            if node.visited:
                color = tuple(c // 2 for c in color)
            elif not node.available:
                color = tuple(c // 3 for c in color)

        if node.available and not node.blocked:
            pygame.draw.circle(surface, (60, 60, 40), pos, self.node_radius + 6)

        pygame.draw.circle(surface, color, pos, self.node_radius)
        pygame.draw.circle(surface, WHITE if not node.blocked else (60, 60, 60),
                           pos, self.node_radius, 2)

        icon = self._get_node_icon(node.node_type)
        icon_color = WHITE
        if node.blocked:
            icon = "X"
            icon_color = (80, 80, 80)

        text = get_font(26).render(icon, True, icon_color)
        surface.blit(text, text.get_rect(center=pos))

        if node.visited:
            check = get_font(18).render("\u2713", True, GREEN)
            surface.blit(check, (pos[0] + 14, pos[1] - 14))

        if self.hovered_node_id == node.node_id and node.available and not node.blocked:
            pygame.draw.circle(surface, YELLOW, pos, self.node_radius + 4, 2)

    def _get_node_icon(self, node_type):
        icons = {
            NodeType.COMBAT: "X",
            NodeType.ELITE: "E",
            NodeType.EVENT: "?",
            NodeType.CAMP: "C",
            NodeType.SHOP: "$",
            NodeType.BOSS: "B",
            NodeType.RESCUE_ANIMAL: "A"
        }
        return icons.get(node_type, "?")

    def _button_surface(self, key, hovered):
        cache_key = (key, hovered)
        if cache_key in self._button_cache:
            return self._button_cache[cache_key]

        surface = None
        if self.assets:
            surface = self.assets.get_ui_button(key, self.BUTTON_WIDTH)
        if surface and hovered:
            surface = surface.copy()
            surface.fill((55, 42, 12), special_flags=pygame.BLEND_RGB_ADD)
        self._button_cache[cache_key] = surface
        return surface

    def _draw_buttons(self, surface):
        for key, rect in self.button_rects.items():
            hovered = self.hovered_button == key
            button_surface = self._button_surface(key, hovered)
            if button_surface:
                surface.blit(button_surface, rect.topleft)
                if hovered:
                    pygame.draw.rect(surface, SERTAO_GOLD, rect, 2,
                                     border_radius=8)
            else:
                draw_sertao_button(
                    surface, rect, self.BUTTON_LABELS.get(key, key.upper()),
                    is_hovered=hovered, font_size=18)

    def _draw_legend(self, surface):
        legend_y = SCREEN_HEIGHT - 78
        left_items = [
            ("combat", "Combate"),
            ("elite", "Elite"),
            ("event", "Evento"),
        ]
        right_items = [
            ("camp", "Acampamento"),
            ("shop", "Loja"),
            ("boss", "Chefe"),
            ("rescue_animal", "Animal"),
        ]
        item_width = 140
        left_start = 610 - len(left_items) * item_width
        right_start = 670

        for group, start_x in ((left_items, left_start),
                               (right_items, right_start)):
            for i, (key, label) in enumerate(group):
                x = start_x + i * item_width
                icon = None
                if self.assets:
                    icon = self.assets.get_node_icon(key, 26)
                if icon is not None:
                    surface.blit(icon, icon.get_rect(midleft=(x, legend_y + 10)))
                else:
                    pygame.draw.circle(
                        surface, NODE_COLORS.get(key, GRAY),
                        (x + 8, legend_y + 10), 8)
                draw_text(surface, label, (x + 30, legend_y),
                          font_size=14, color=WHITE)

    def _draw_tooltip(self, surface):
        if self.tooltip_alpha <= 0 or self.hovered_node_id is None:
            return

        node = self.map_gen.nodes.get(self.hovered_node_id)
        if not node:
            return

        tooltip_info = NODE_TOOLTIPS.get(node.node_type)
        if not tooltip_info:
            return

        pos = self.node_positions.get(self.hovered_node_id)
        if not pos:
            return

        items = [(tooltip_info["title"], 24, YELLOW)] + [
            (line, 19, CREAM) for line in tooltip_info["lines"]]

        padding = 14
        max_text_width, text_height = measure_block(items, line_spacing=6)
        if node.node_type == NodeType.BOSS:
            text_height += get_font(15).get_height() + 10
        width = max_text_width + padding * 2
        height = padding * 2 + text_height

        tx = min(pos[0] + 35, SCREEN_WIDTH - width - 10)
        ty = pos[1] - height - 10
        if ty < 10:
            # Not enough room above (top floors): show below the node instead.
            ty = pos[1] + 45
        ty = max(10, min(ty, SCREEN_HEIGHT - height - 10))

        tooltip_rect = pygame.Rect(tx, ty, width, height)

        bg_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        bg_color = (20, 18, 30, self.tooltip_alpha)
        border_color_r = min(255, int(200 * (self.tooltip_alpha / self.tooltip_max_alpha)))
        border_color_g = min(255, int(180 * (self.tooltip_alpha / self.tooltip_max_alpha)))
        border_color_b = min(255, int(50 * (self.tooltip_alpha / self.tooltip_max_alpha)))

        pygame.draw.rect(bg_surf, bg_color, (0, 0, width, height), border_radius=8)
        surface.blit(bg_surf, tooltip_rect.topleft)

        border_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (border_color_r, border_color_g, border_color_b, self.tooltip_alpha),
                         (0, 0, width, height), 2, border_radius=8)
        surface.blit(border_surf, tooltip_rect.topleft)

        inner = pygame.Rect(tx, ty, width, height)
        if node.node_type == NodeType.BOSS:
            body_items = list(items)
            body_items.append(("", 10, CREAM))
            body_items.append(("Libera animal ao vencer!", 15, GREEN))
            draw_text_block_colored(surface, body_items, inner, line_spacing=2)
        else:
            draw_text_block_colored(surface, items, inner, line_spacing=2)
