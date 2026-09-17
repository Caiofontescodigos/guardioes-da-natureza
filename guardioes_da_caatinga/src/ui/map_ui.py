import pygame
import time
from config import (WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN,
                    CREAM, SCREEN_WIDTH, SCREEN_HEIGHT, NODE_COLORS, BIOME_COLORS)
from src.ui.components import draw_text
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
    def __init__(self, map_generator, biome_id, assets=None):
        self.map_gen = map_generator
        self.biome_id = biome_id
        self.assets = assets
        self.node_radius = 22
        self.node_positions = {}
        self.calculate_positions()

        self.hover_start_time = None
        self.hovered_node_id = None
        self.tooltip_alpha = 0
        self.tooltip_max_alpha = 220
        self.tooltip_fade_speed = 8

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
            for node_id, pos in self.node_positions.items():
                node = self.map_gen.nodes.get(node_id)
                if node and node.available and not node.blocked:
                    dist = ((event.pos[0] - pos[0]) ** 2 + (event.pos[1] - pos[1]) ** 2) ** 0.5
                    if dist <= self.node_radius + 5:
                        self.hover_start_time = None
                        self.hovered_node_id = None
                        self.tooltip_alpha = 0
                        return node_id
        return None

    def _handle_hover(self, mouse_pos):
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

        if self.hovered_node_id and self.hover_start_time:
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

        draw_text(surface, f"Mapa - {self.biome_id.replace('_', ' ').title()}",
                  (SCREEN_WIDTH // 2, 20), font_size=32, color=YELLOW, center=True)

        for node_id, node in self.map_gen.nodes.items():
            if node_id in self.node_positions:
                self._draw_connections(surface, node)

        for node_id, node in self.map_gen.nodes.items():
            if node_id in self.node_positions:
                self._draw_node(surface, node)

        self._draw_legend(surface)
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

    def _draw_node(self, surface, node):
        pos = self.node_positions.get(node.node_id)
        if not pos:
            return

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
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)

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

    def _draw_legend(self, surface):
        legend_y = SCREEN_HEIGHT - 60
        items = [
            ("X Combate", NODE_COLORS["combat"]),
            ("E Elite", NODE_COLORS["elite"]),
            ("? Evento", NODE_COLORS["event"]),
            ("C Acampamento", NODE_COLORS["camp"]),
            ("$ Loja", NODE_COLORS["shop"]),
            ("B Chefe", NODE_COLORS["boss"]),
            ("A Animal", NODE_COLORS.get("rescue_animal", (100, 200, 160))),
        ]

        total_width = len(items) * 150
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, (text, color) in enumerate(items):
            x = start_x + i * 150
            pygame.draw.circle(surface, color, (x + 8, legend_y + 10), 8)
            draw_text(surface, text, (x + 20, legend_y), font_size=14, color=WHITE)

    def _draw_tooltip(self, surface):
        if self.tooltip_alpha <= 0 or not self.hovered_node_id:
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
        ty = max(pos[1] - height - 10, 10)

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
