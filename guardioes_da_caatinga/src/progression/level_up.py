import random
from config import load_upgrades, SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, CREAM, BLUE, GRAY
from src.ui.components import Button, draw_text


class LevelUpSystem:
    def __init__(self):
        self.upgrades = load_upgrades()
        self.upgrades_per_choice = 3

    def get_available_upgrades(self, animal, count=None):
        if count is None:
            count = self.upgrades_per_choice

        available = list(self.upgrades.values())
        selected = random.sample(available, min(count, len(available)))
        return selected

    def apply_upgrade(self, animal, upgrade):
        old_atk = animal.base_attack
        old_def = animal.base_defense
        old_spd = animal.base_speed
        old_hp = animal.max_hp
        animal.apply_permanent_upgrade(upgrade["effect"], upgrade["value"])
        print(f"[UPGRADE] {animal.name} recebeu: {upgrade['name']}")
        print(f"  HP: {old_hp} -> {animal.max_hp}")
        print(f"  ATK: {old_atk} -> {animal.base_attack}")
        print(f"  DEF: {old_def} -> {animal.base_defense}")
        print(f"  SPD: {old_spd} -> {animal.base_speed}")
        return True

    def should_offer_upgrade(self, animal):
        return True


class UpgradeUI:
    def __init__(self, upgrades, on_select):
        self.upgrades = upgrades
        self.on_select = on_select
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        self.buttons = []
        btn_width = 300
        btn_height = 120
        start_x = SCREEN_WIDTH // 2 - btn_width // 2
        start_y = 200

        for i, upgrade in enumerate(self.upgrades):
            y = start_y + i * (btn_height + 20)
            btn = Button(start_x, y, btn_width, btn_height, "", BLUE)
            btn.upgrade = upgrade
            self.buttons.append(btn)

    def handle_event(self, event):
        for button in self.buttons:
            if button.handle_event(event):
                return button.upgrade
        return None

    def draw(self, surface):
        surface.fill((20, 15, 30))
        draw_text(surface, "Melhoria Disponivel!", (SCREEN_WIDTH // 2, 80), font_size=48, color=YELLOW, center=True)
        draw_text(surface, "Escolha uma melhoria para seu animal",
                 (SCREEN_WIDTH // 2, 140), font_size=24, color=CREAM, center=True)

        for button in self.buttons:
            button.draw(surface)
            upgrade = button.upgrade
            x, y = button.rect.topleft

            draw_text(surface, upgrade["name"], (x + 150, y + 25), font_size=24, color=WHITE, center=True)
            draw_text(surface, upgrade["description"], (x + 150, y + 60), font_size=18, color=CREAM, center=True)
            draw_text(surface, f"Categoria: {upgrade['category']}", (x + 150, y + 90), font_size=16, color=GRAY, center=True)
