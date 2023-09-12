import game

from pygame import Surface


class Fade:
    def __init__(self, color, time):
        self.surface = Surface(game.screen.display_size)
        self.surface.fill(color)
        self.time = time
        self.counter = time

    def update(self, dt):
        if self.counter > 0.0:
            self.surface.set_alpha(int(255.0 * self.counter / self.time))
            game.screen.draw(self.surface, (0, 0))
            self.counter -= dt
