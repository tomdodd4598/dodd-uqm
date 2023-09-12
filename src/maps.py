import math
import numpy as np
import pygame as pg
import time as pt

import assets
import constants
import data
import game
import helpers
import keys

from pygame import Rect, Surface
from sprites import Sprite, HUDSprite


class Element:
    def __init__(self, name, image, scale, pos, angle):
        self.name = name
        self.sprite = ElementSprite(name, image, scale, pos, angle)

    def draw(self, camera, minimap, paused):
        self.sprite.draw(camera)

    def minimap_draw(self, camera, paused):
        pass


class SolarSystemElement(Element):
    def __init__(self, name, image, scale, pos, angle, system):
        super().__init__(name, image, scale, pos, angle)
        self.system = system


class NaturalOrbitingElement(Element):
    def highlight(self, offset, orbit_number, pulse_frequency, pointer_rect, highlight_rect, ellipse_color):
        pressed_keys = pg.key.get_pressed()
        if keys.contains_number(pressed_keys, orbit_number):
            sin = math.sin(16.0 * pulse_frequency * pt.time())
            if self.sprite.rect.move(*offset).colliderect(game.screen.display_rect):
                thickness = int(2.5 + 1.5 * sin)
                pg.draw.ellipse(game.screen.display, ellipse_color, highlight_rect.move(*offset), thickness)
            else:
                pointer_rect = pointer_rect.move(*offset)
                cx, cy = pointer_rect.centerx, pointer_rect.centery
                h_w, h_h = 0.5 * game.screen.display_width, 0.5 * game.screen.display_height
                x_ratio = 1.0 if cx == h_w else abs((h_w - 0.0 * pointer_rect.w) / (cx - h_w))
                y_ratio = 1.0 if cy == h_h else abs((h_h - 0.0 * pointer_rect.h) / (cy - h_h))
                dist_ratio = min(x_ratio, y_ratio)
                pointer_rect.centerx = h_w + dist_ratio * (cx - h_w)
                pointer_rect.centery = h_h + dist_ratio * (cy - h_h)

                surf = Surface(Rect(pointer_rect).size, pg.SRCALPHA)
                pg.draw.ellipse(surf, (*ellipse_color, int(159.375 + 95.625 * sin)), surf.get_rect())
                game.screen.display.blit(surf, pointer_rect)
                # pg.draw.ellipse(game.screen.display, ellipse_color, pointer_rect)


class SolarSystemStarElement(SolarSystemElement):
    def __init__(self, name, image, scale, pos, angle, system):
        super().__init__(name, image, scale, pos, angle, system)
        self.minimap_sprite = HUDSprite(image, (helpers.solar_system_minimap_f(system) * scale[0],), game.screen.minimap_center)

    def minimap_draw(self, camera, paused):
        self.minimap_sprite.draw(camera)


class SolarSystemPlanetElement(SolarSystemElement, NaturalOrbitingElement):
    def __init__(self, name, image, sprite_scale, orbit_scale, system, planet, time, minimap_scale):
        orbit_size = orbit_scale * game.screen.display_size
        self.orbit_angle = planet.initial_angle + 0.0172017 * time * math.sqrt(system.mass / (planet.orbit * planet.orbit * planet.orbit))
        cos_sin_orbit_angle = np.array([math.cos(self.orbit_angle), math.sin(self.orbit_angle)])
        super().__init__(name, image, sprite_scale, orbit_size * cos_sin_orbit_angle, planet.tilt, system)

        self.ellipse_rect = Rect(-orbit_size, 2.0 * orbit_size)
        rect = self.sprite.rect
        self.pointer_rect = Rect(rect.x, rect.y, rect.w, rect.h)
        self.highlight_rect = Rect(rect.x - 8, rect.y - 8, rect.w + 16, rect.h + 16)

        minimap_orbit_size = game.screen.minimap_size_mult * minimap_scale * orbit_size
        minimap_orbit_pos = game.screen.minimap_center + minimap_orbit_size * cos_sin_orbit_angle
        self.minimap_sprite = HUDSprite(image, (minimap_scale * sprite_scale[0],), minimap_orbit_pos)

        self.minimap_ellipse_rect = Rect(game.screen.minimap_center - minimap_orbit_size, 2.0 * minimap_orbit_size)

        self.planet = planet
        self.ellipse_color = helpers.temperature_color(planet.temperature)

    def draw(self, camera, minimap, paused):
        offset = -camera[0], -camera[1]
        pg.draw.ellipse(game.screen.display, self.ellipse_color, self.ellipse_rect.move(*offset), 1)
        super().draw(camera, minimap, paused)
        if not paused:
            freq = 0.25 / math.sqrt(helpers.solar_system_planet_radius_f(self.planet))
            self.highlight(offset, self.planet.number, freq, self.pointer_rect, self.highlight_rect, self.ellipse_color)

    def minimap_draw(self, camera, paused):
        pg.draw.ellipse(game.screen.display, self.ellipse_color, self.minimap_ellipse_rect, 1)
        self.minimap_sprite.draw(camera)


class PlanetarySystemElement(Element):
    def __init__(self, name, image, scale, pos, angle, planet):
        super().__init__(name, image, scale, pos, angle)
        self.planet = planet


class PlanetarySystemPlanetElement(PlanetarySystemElement, NaturalOrbitingElement):
    def __init__(self, name, image, scale, pos, angle, system, planet, time):
        super().__init__(name, image, scale, pos, angle, planet)
        self.orbit_angle = None
        # rect = self.sprite.rect
        # self.pointer_rect = Rect(rect.x, rect.y, rect.w, rect.h)
        # self.highlight_rect = Rect(rect.x - 8, rect.y - 8, rect.w + 16, rect.h + 16)
        self.ellipse_color = helpers.temperature_color(planet.temperature)
        line_angle = planet.initial_angle + 0.0172017 * time * math.sqrt(system.mass / (planet.orbit * planet.orbit * planet.orbit))
        display_mult = game.screen.display_max_dim / game.screen.display_min_dim
        self.line_pos = display_mult * np.array([game.screen.display_width * math.sin(line_angle), -game.screen.display_height * math.cos(line_angle)])

    def draw(self, camera, minimap, paused):
        pg.draw.line(game.screen.display, self.ellipse_color, self.line_pos - camera, -self.line_pos - camera, 1)
        super().draw(camera, minimap, paused)
        # if not paused:
        # freq = 0.25 / math.sqrt(helpers.planetary_system_moon_radius_f(self.planet, self.planet))
        # self.highlight((-camera[0], -camera[1]), 0, freq, self.pointer_rect, self.highlight_rect, self.ellipse_color)


class PlanetarySystemMoonElement(PlanetarySystemElement, NaturalOrbitingElement):
    def __init__(self, name, image, sprite_scale, orbit_scale, planet, moon, time):
        orbit_size = game.screen.display_size * orbit_scale
        self.orbit_angle = moon.initial_angle + 971.903 * time * math.sqrt(planet.mass / (moon.orbit * moon.orbit * moon.orbit))
        cos_sin_orbit_angle = np.array([math.cos(self.orbit_angle), math.sin(self.orbit_angle)])
        super().__init__(name, image, sprite_scale, orbit_size * cos_sin_orbit_angle, planet.tilt, planet)

        self.ellipse_rect = Rect(-orbit_size, 2.0 * orbit_size)
        rect = self.sprite.rect
        self.pointer_rect = Rect(rect.x, rect.y, rect.w, rect.h)
        self.highlight_rect = Rect(rect.x - 8, rect.y - 8, rect.w + 16, rect.h + 16)

        self.moon = moon
        self.ellipse_color = helpers.temperature_color(moon.temperature)

    def draw(self, camera, minimap, paused):
        offset = -camera[0], -camera[1]
        pg.draw.ellipse(game.screen.display, self.ellipse_color, self.ellipse_rect.move(*offset), 1)
        super().draw(camera, minimap, paused)
        if not paused:
            freq = 0.25 / math.sqrt(helpers.planetary_system_moon_radius_f(self.planet, self.moon))
            self.highlight(offset, self.moon.number, freq, self.pointer_rect, self.highlight_rect, self.ellipse_color)


class HyperSpaceElement(Element):
    def __init__(self, name, image, scale, coords, angle):
        super().__init__(name, image, scale, helpers.coords_to_pos(coords), angle)
        self.coords = coords


class HyperSpaceSystemElement(HyperSpaceElement):
    def __init__(self, name, image, scale, coords, angle):
        super().__init__(name, image, scale, coords, angle)


class ElementSprite(Sprite):
    def __init__(self, name, image, scale, pos, angle):
        super().__init__(image, scale, pos)
        self.name = name
        self.base_image = self.image
        self.angle = angle
        self.set_rect()
        self.radius = self.get_collision_radius()

    def set_rect(self):
        super().set_rect()
        self.image, self.rect = helpers.rotate(self.base_image, self.rect, self.angle, self.rect.center)

    def get_collision_radius(self):
        return 0.5 * super().get_collision_radius()

    def rect_blit(self, camera):
        return self.rect.move(-camera[0], -camera[1])


class Map:
    def __init__(self):
        self.elems = []


class TrueSpaceMap(Map):
    def __init__(self):
        super().__init__()


class SolarSystemMap(TrueSpaceMap):
    def __init__(self, name, time):
        super().__init__()
        self.system = data.systems[name]

        star_image = get_truespace_star_image(self.system)
        cbrt_star_f = helpers.solar_system_star_f(self.system) ** constants.inv_3
        self.scale = 1.0 / (cbrt_star_f * cbrt_star_f)
        self.half_width = self.scale * helpers.solar_system_width_f(self.system)
        self.half_height = self.scale * helpers.solar_system_height_f(self.system)
        self.minimap_scale = helpers.solar_system_minimap_f(self.system) / self.scale
        self.elems.append(SolarSystemStarElement(name, star_image, (cbrt_star_f,), np.zeros(2), 0.0, self.system))

        for planet in self.system.planets:
            planet_image = get_planet_image(planet)
            planet_radius_scale = self.scale * helpers.solar_system_planet_radius_f(planet)
            planet_orbit_scale = self.scale * helpers.solar_system_orbit_f(self.system, planet)
            self.elems.append(SolarSystemPlanetElement(planet.name, planet_image, (planet_radius_scale,), planet_orbit_scale, self.system, planet, time, self.minimap_scale))


class PlanetarySystemMap(TrueSpaceMap):
    def __init__(self, system, planet, time):
        super().__init__()
        self.system = system
        self.planet = planet

        planet_image = get_planet_image(planet)
        self.half_width = helpers.planetary_system_width_f(planet)
        self.half_height = helpers.planetary_system_height_f(planet)
        self.scale = 0.5 * min(game.screen.display_width / self.half_width,
                               game.screen.display_height / self.half_height)
        self.half_width *= self.scale
        self.half_height *= self.scale
        planet_scale = self.scale * helpers.planetary_system_planet_f(planet)
        self.elems.append(PlanetarySystemPlanetElement(planet.name, planet_image, (planet_scale,), np.zeros(2), planet.tilt, system, planet, time))

        for moon in planet.moons:
            moon_image = get_planet_image(moon)
            moon_radius_scale = self.scale * helpers.planetary_system_moon_radius_f(planet, moon)
            moon_orbit_scale = self.scale * helpers.planetary_system_orbit_f(planet, moon)
            self.elems.append(PlanetarySystemMoonElement(moon.name, moon_image, (moon_radius_scale,), moon_orbit_scale, planet, moon, time))


color_map = {
    'r': 'red',
    'o': 'orange',
    'y': 'yellow',
    'g': 'green',
    'w': 'white',
    'b': 'blue',
}

size_map = {
    's': 'small',
    'm': 'medium',
    'l': 'large',
}


def get_truespace_star_image(star):
    return assets.get_truespace_star(color_map[star.color])


def get_planet_image(planet):
    return assets.get_planet(planet.type_name, planet.orbit)


class HyperSpaceMap(Map):
    def __init__(self):
        super().__init__()
        for system in data.systems.values():
            image = get_hyperspace_star_image(system)
            self.elems.append(HyperSpaceSystemElement(system.name, image, 2.0, system.coords, 0.0))


def get_hyperspace_star_image(star):
    return assets.get_hyperspace_star(color_map[star.color], size_map[star.size])
