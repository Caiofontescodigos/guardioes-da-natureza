"""Small generated sound effects (no audio files required)."""

import math
from array import array

import pygame


class SfxManager:
    def __init__(self, settings=None):
        settings = settings or {}
        try:
            self.volume = max(0.0, min(1.0, float(
                settings.get("sfx_volume", 0.8))))
        except (TypeError, ValueError):
            self.volume = 0.8
        self._ping = None
        self._build_ping()

    def _build_ping(self):
        init = pygame.mixer.get_init()
        if not init:
            return
        frequency, size, channels = init
        if size != -16:
            return
        try:
            samples = array("h")
            sample_rate = int(frequency)
            duration = 0.34
            total = int(sample_rate * duration)
            amplitude = 0.32 * 32767
            for index in range(total):
                t = index / sample_rate
                if t < 0.14:
                    note_t = t
                    note_frequency = 880.0
                else:
                    note_t = t - 0.14
                    note_frequency = 1320.0
                attack = min(1.0, note_t / 0.008)
                release = max(0.0, 1.0 - note_t / 0.20)
                envelope = attack * release
                value = int(amplitude * envelope *
                            math.sin(2 * math.pi * note_frequency * t))
                for _ in range(max(1, channels)):
                    samples.append(value)
            sound = pygame.mixer.Sound(buffer=samples.tobytes())
            sound.set_volume(self.volume)
            self._ping = sound
        except (pygame.error, ValueError, MemoryError) as e:
            print(f"[SFX] Nao foi possivel gerar o ping: {e}")
            self._ping = None

    def set_volume(self, volume):
        try:
            self.volume = max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            return
        if self._ping:
            self._ping.set_volume(self.volume)

    def play_achievement(self):
        if not self._ping or self.volume <= 0:
            return
        try:
            self._ping.play()
        except pygame.error:
            pass
