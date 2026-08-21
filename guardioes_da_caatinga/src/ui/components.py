import pygame
from config import WHITE, BLACK, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, BROWN, CREAM, SCREEN_WIDTH, SCREEN_HEIGHT

class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=None, text_color=WHITE, font_size=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color or self._lighten_color(color)
        self.text_color = text_color
        self.font_size = font_size
        self.is_hovered = False
        self.is_clicked = False
        self.enabled = True
        self.font = None

    def _lighten_color(self, color):
        return tuple(min(255, c + 40) for c in color)

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_clicked = True
                return True
        return False

    def draw(self, surface):
        if not self.enabled:
            color = GRAY
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color

        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)

        if self.font is None:
            self.font = pygame.font.Font(None, self.font_size)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def reset_click(self):
        self.is_clicked = False

class HealthBar:
    def __init__(self, x, y, width, height, max_hp, current_hp):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.bg_color = DARK_GRAY
        self.fill_color = GREEN
        self.low_color = RED
        self.border_color = BLACK

    def update(self, current_hp, max_hp=None):
        self.current_hp = current_hp
        if max_hp is not None:
            self.max_hp = max_hp

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect)
        fill_width = int((self.current_hp / self.max_hp) * self.rect.width) if self.max_hp > 0 else 0
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        ratio = self.current_hp / self.max_hp if self.max_hp > 0 else 0
        color = self.low_color if ratio < 0.3 else self.fill_color
        pygame.draw.rect(surface, color, fill_rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)

        font = pygame.font.Font(None, 18)
        text = font.render(f"{self.current_hp}/{self.max_hp}", True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

class Tooltip:
    def __init__(self):
        self.visible = False
        self.text = ""
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.font = pygame.font.Font(None, 20)
        self.padding = 10

    def show(self, text, pos):
        self.text = text
        self.visible = True
        lines = text.split('\n')
        max_width = max(self.font.size(line)[0] for line in lines) + self.padding * 2
        height = len(lines) * 22 + self.padding * 2
        x = min(pos[0] + 15, SCREEN_WIDTH - max_width - 10)
        y = min(pos[1] + 15, SCREEN_HEIGHT - height - 10)
        self.rect = pygame.Rect(x, y, max_width, height)

    def hide(self):
        self.visible = False

    def draw(self, surface):
        if not self.visible:
            return
        pygame.draw.rect(surface, (30, 30, 30), self.rect, border_radius=5)
        pygame.draw.rect(surface, YELLOW, self.rect, 2, border_radius=5)
        lines = self.text.split('\n')
        y_offset = self.rect.y + self.padding
        for line in lines:
            text_surface = self.font.render(line, True, WHITE)
            surface.blit(text_surface, (self.rect.x + self.padding, y_offset))
            y_offset += 22

class Panel:
    def __init__(self, x, y, width, height, color=(40, 40, 60)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        pygame.draw.rect(surface, GRAY, self.rect, 2, border_radius=10)

class Label:
    def __init__(self, x, y, text, font_size=24, color=WHITE):
        self.x = x
        self.y = y
        self.text = text
        self.font_size = font_size
        self.color = color
        self.font = None

    def set_text(self, text):
        self.text = text

    def draw(self, surface, center=False):
        if self.font is None:
            self.font = pygame.font.Font(None, self.font_size)
        text_surface = self.font.render(self.text, True, self.color)
        if center:
            text_rect = text_surface.get_rect(center=(self.x, self.y))
        else:
            text_rect = text_surface.get_rect(topleft=(self.x, self.y))
        surface.blit(text_surface, text_rect)

def draw_text(surface, text, pos, font_size=24, color=WHITE, center=False):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    if center:
        text_rect = text_surface.get_rect(center=pos)
    else:
        text_rect = text_surface.get_rect(topleft=pos)
    surface.blit(text_surface, text_rect)
    return text_rect

def draw_bar(surface, x, y, width, height, current, maximum, fill_color=GREEN, bg_color=DARK_GRAY, border=True):
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    fill_width = int((current / maximum) * width) if maximum > 0 else 0
    ratio = current / maximum if maximum > 0 else 0
    color = RED if ratio < 0.3 else fill_color
    pygame.draw.rect(surface, color, (x, y, fill_width, height))
    if border:
        pygame.draw.rect(surface, BLACK, (x, y, width, height), 2)
    font = pygame.font.Font(None, 18)
    text = font.render(f"{current}/{maximum}", True, WHITE)
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text, text_rect)

def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
