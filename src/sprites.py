import game
import pygame as pg

from pygame import Surface


class Sprite(pg.sprite.Sprite):
    def __init__(self, image, scale, pos):
        super().__init__()
        self.image = image if isinstance(image, Surface) else pg.image.load(image).convert_alpha()

        scaled_rect = self.image.get_rect()
        if isinstance(scale, (int, float)):
            self.scale = scale
        else:
            image_dim = scaled_rect.width if game.screen.display_min_dim_index == 0 else scaled_rect.height
            self.scale = scale[0] * game.screen.display_min_dim / image_dim
        if self.scale != 1.0:
            scaled_size = self.scale * scaled_rect.width, self.scale * scaled_rect.height
            self.image = pg.transform.smoothscale(self.image, scaled_size)

        self.pos = pos

    def set_rect_pos(self):
        self.rect.center = (self.pos[0], self.pos[1])

    def set_rect(self):
        self.rect = self.image.get_rect()
        self.set_rect_pos()

    def get_collision_radius(self):
        return 0.5 * max(self.rect.width, self.rect.height)

    def rect_blit(self, camera):
        raise NotImplementedError

    def draw(self, camera):
        rect_blit = self.rect_blit(camera)
        if rect_blit.colliderect(game.screen.display_rect):
            game.screen.draw(self.image, rect_blit)


class HUDSprite(Sprite):
    def __init__(self, image, scale, pos):
        super().__init__(image, scale, pos)
        self.set_rect()

    def rect_blit(self, camera):
        return self.rect
