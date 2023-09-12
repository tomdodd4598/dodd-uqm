import math
import numpy as np
import pygame as pg
import time as pt

import constants
import game
import helpers
import keys

from abc import ABCMeta
from sprites import Sprite


class Ship(Sprite, metaclass=ABCMeta):
    def __init__(self, image, scale, pos, space, engine, mass, moi, area, vel, angle, ang_vel):
        super().__init__(image, scale, pos)
        self.base_image = self.image
        self.space = space
        self.engine = engine
        self.mass = mass
        self.moi = moi
        self.area = area
        self.vel = vel
        self.angle = angle
        self.ang_vel = ang_vel
        self.dir = np.array([np.cos(angle), np.sin(angle)])
        self.set_rect()
        self.radius = self.get_collision_radius()

    def set_rect_pos(self):
        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

    def set_rect(self):
        super().set_rect()
        self.image, self.rect = helpers.rotate(self.base_image, self.rect, self.angle)

    def get_collision_radius(self):
        return constants.inv_sqrt2 * super().get_collision_radius()

    def rect_blit(self, camera):
        return self.rect.move(-camera[0], -camera[1])

    def update(self, pressed, target_pos, dt):
        raise NotImplementedError

    def autopilot_update(self, target_pos, dt):
        target_dir = helpers.normalize(target_pos - self.pos)
        mult = 0.5 + 0.5 * np.dot(target_dir, np.array([math.cos(self.angle), math.sin(self.angle)]))
        mult **= 24.0
        long_mult = mult
        target_angle = helpers.positive_fmod(math.atan2(target_dir[1], target_dir[0]), constants.two_pi)
        angle_diff = np.fmod(constants.two_pi + target_angle - self.angle, constants.two_pi)
        lat_mult = 1.0 - mult if angle_diff < math.pi else mult - 1.0
        modifier1, modifier2 = False, True
        self.engine.update_ship(self, self.space, lat_mult, long_mult, modifier1, modifier2, dt)

    def update_dir(self):
        self.dir = np.array([np.cos(self.angle), np.sin(self.angle)])

    def minimap_draw(self, minimap_scale):
        color = (255, 255, int(128.0 + 127.5 * math.sin(16.0 * pt.time())))
        pos = game.screen.minimap_center + game.screen.minimap_size_mult * minimap_scale * self.pos
        if game.screen.minimap_rect.collidepoint(pos[0], pos[1]):
            pg.draw.circle(game.screen.display, color, pos, max(1.0, minimap_scale * self.radius))


class PlayerShip(Ship):
    def __init__(self, player, image, scale, pos, space, mass, moi, area, vel, angle, ang_vel):
        super().__init__(image, scale, pos, space, player.engine, mass, moi, area, vel, angle, ang_vel)
        self.player = player

    def rect_blit(self, camera):
        return self.rect.move(-camera[0], -camera[1])

    def update(self, pressed, target_pos, dt):
        if target_pos is None:
            lat_mult, long_mult = 0.0, 0.0
            modifier1, modifier2 = False, False

            if keys.contains_up(pressed):
                long_mult += 1.0
            if keys.contains_left(pressed):
                lat_mult -= 1.0
            if keys.contains_down(pressed):
                long_mult -= 1.0
            if keys.contains_right(pressed):
                lat_mult += 1.0
            if keys.contains_shift(pressed):
                modifier1 = True
            if keys.contains_ctrl(pressed):
                modifier2 = True

            self.engine.update_ship(self, self.space, lat_mult, long_mult, modifier1, modifier2, dt)
        else:
            self.autopilot_update(target_pos, dt)

        self.update_dir()
        self.set_rect()


class NPCShip(Ship, metaclass=ABCMeta):
    def __init__(self, image, scale, pos, space, engine, mass, moi, area, vel, angle, ang_vel):
        super().__init__(image, scale, pos, space, engine, mass, moi, area, vel, angle, ang_vel)
        self.engine = engine


class InterceptShip(NPCShip):
    def __init__(self, image, scale, pos, space, engine, mass, moi, area, vel, angle, ang_vel, rotate):
        self.rotate = rotate
        super().__init__(image, scale, pos, space, engine, mass, moi, area, vel, angle, ang_vel)

    def set_rect(self):
        if self.rotate:
            super().set_rect()
        else:
            Sprite.set_rect(self)
            self.image, self.rect = helpers.rotate(self.base_image, self.rect, 0.0)

    def update(self, pressed, target_pos, dt):
        self.autopilot_update(target_pos, dt)
        self.update_dir()
        self.set_rect()
