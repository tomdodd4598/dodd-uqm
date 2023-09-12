import assets
import game
import helpers
import numpy as np
import random

from sprites import Sprite, HUDSprite


class BackgroundSprite(Sprite):
    def __init__(self, image, scale, pos, dist, rand):
        super().__init__(image, scale, pos)
        self.dist = dist
        self.rand = rand
        self.padding = 0
        self.set_rect()

    def set_rect(self):
        super().set_rect()
        self.padding = max(*self.image.get_size())

    def rect_blit(self, camera):
        pass

    def draw(self, camera):
        if self.dist is None:
            game.screen.draw(self.image, self.rect)
        else:
            offset = camera / self.dist
            pos_blit = self.pos - offset
            display_size = game.screen.display_size

            bounded_x = helpers.extend_bounded(pos_blit[0], display_size[0], self.padding)
            bounded_y = helpers.extend_bounded(pos_blit[1], display_size[1], self.padding)

            if not bounded_x:
                self.pos[0] = offset[0] + helpers.extended_mod(pos_blit[0], display_size[0], self.padding)
                if self.rand:
                    self.pos[1] = offset[1] + random.random() * display_size[1]

            if not bounded_y:
                if self.rand:
                    self.pos[0] = offset[0] + random.random() * display_size[0]
                self.pos[1] = offset[1] + helpers.extended_mod(pos_blit[1], display_size[1], self.padding)

            pos_blit = helpers.extended_mod(pos_blit, display_size, self.padding)
            rect_blit = self.rect.copy()
            rect_blit.update(pos_blit[0], pos_blit[1], rect_blit.width, rect_blit.height)
            game.screen.draw(self.image, rect_blit)


class BackgroundStar(BackgroundSprite):
    def __init__(self, image, scale, pos, dist, rand):
        super().__init__(image, scale, pos, dist, rand)


truespace_background_star_names = [assets.get_truespace_background_star(name) for name in [
    '010c', '010d', '010e', '012c', '012d', '012e', '019b', '019c', '020a', '020b', '021a', '021b'
]]

hyperspace_background_star_names = [assets.get_hyperspace_background_star(name) for name in [
    '010c', '010d', '010e', '019b', '019c', '019d'
]]

quasispace_background_star_names = [assets.get_quasispace_background_star(name) for name in [
    '010c', '010d', '010e', '019b', '019c', '019d'
]]


def random_background_star(scale, dist, rand, name_list):
    pos = np.array([random.random(), random.random()]) * game.screen.display_size
    return BackgroundStar(random.choice(name_list), scale, pos, dist, rand)


def random_truespace_background_star(scale, dist):
    return random_background_star(scale, dist, False, truespace_background_star_names)


def random_hyperspace_background_star(scale, dist):
    return random_background_star(scale, dist, True, hyperspace_background_star_names)


def random_quasispace_background_star(scale, dist):
    return random_background_star(scale, dist, True, quasispace_background_star_names)


def random_minimap_background_star(scale, name_list):
    minimap_rect = game.screen.minimap_rect
    pos = np.array([minimap_rect.x, minimap_rect.y]) + np.array([random.random(), random.random()]) * np.array([minimap_rect.w, minimap_rect.h])
    return HUDSprite(random.choice(name_list), scale, pos)


def random_truespace_minimap_background_star(scale):
    return random_minimap_background_star(scale, truespace_background_star_names)


def random_hyperspace_minimap_background_star(scale):
    return random_minimap_background_star(scale, hyperspace_background_star_names)


def random_quasispace_minimap_background_star(scale):
    return random_minimap_background_star(scale, quasispace_background_star_names)
