"""BestiaryManager -- single source of truth for the Bestiario.

Animals are considered discovered once they are unlocked. ``unlocked_animals``
is the authoritative list (the same list used by the rest of the game), so the
Bestiario can never desync from the player's actual animal collection.

Creatures (enemies) are tracked in ``creatures_discovered``.
"""


class BestiaryManager:
    def __init__(self, save_manager):
        self.save_manager = save_manager

    def register_animal(self, save_data, animal_id):
        was_discovered = self.is_animal_discovered(save_data, animal_id)
        save_data = self.save_manager.add_unlocked_animal(save_data, animal_id)
        is_new = not was_discovered
        return save_data, is_new

    def is_animal_discovered(self, save_data, animal_id):
        return animal_id in save_data.get("unlocked_animals", [])

    def register_creature(self, save_data, creature_id):
        return self.save_manager.discover_creature(save_data, creature_id)

    def is_creature_discovered(self, save_data, creature_id):
        return self.save_manager.is_creature_discovered(save_data, creature_id)

    def get_discovered_animals(self, save_data):
        return list(save_data.get("unlocked_animals", []))

    def get_discovered_creatures(self, save_data):
        return list(save_data.get("creatures_discovered", []))