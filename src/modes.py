import math
import numpy as np
import pygame as pg
import random

import backgrounds
import constants
import data
import helpers
import game
import spaces

from abc import ABCMeta
from dataclasses import dataclass

from engines import NPCEngine
from fades import Fade
from maps import HyperSpaceMap, SolarSystemMap, PlanetarySystemMap, HyperSpaceSystemElement, NaturalOrbitingElement
from ships import InterceptShip


@dataclass
class DummyTarget:
    name: str


def search_convert(s):
    if not s:
        return ''
    for k, v in helpers.roman_numeral_map.items():
        s = s.replace(str(k), v)
    s = s.split('-')
    s, moon = s[0].title().split(), '' if len(s) == 1 else f'-{s[1]}'
    planet, upper = '', s[-1].upper()
    if upper in helpers.roman_numeral_inv_map.keys():
        s[-1] = upper
    s = ' '.join(s)
    return f'{s}{planet}{moon}'


def get_planet_number(system_name, planet_name):
    planet_suffix = planet_name[len(system_name):].strip().split('-')[0]
    return int(planet_suffix) if planet_suffix.isnumeric() else helpers.roman_numeral_inv_map[planet_suffix]


def get_planet_names(system):
    return [f'{system.name} {x}' for x in get_planet_suffixes(system)]


def get_planet_search_names(system):
    return [f'{system.name.upper()} {x}' for x in get_planet_search_suffixes(system)]


def get_planet_suffixes(system):
    return [x for x in helpers.roman_numerals[:len(system.planets)]]


def get_planet_search_suffixes(system):
    suffixes = get_planet_suffixes(system)
    suffixes.extend(str(x + 1) for x in range(len(system.planets)))
    return suffixes


def get_moon_names(planet):
    return [f'{planet.system.name} {x}' for x in get_moon_suffixes(planet)]


def get_moon_search_names(planet):
    return [f'{planet.system.name.upper()} {x}' for x in get_moon_search_suffixes(planet)]


def get_moon_suffixes(planet):
    return [f'{helpers.roman_numeral_map[planet.number]}-{x}' for x in get_moon_letters(planet)]


def get_moon_search_suffixes(planet):
    suffixes = get_moon_suffixes(planet)
    suffixes.extend(f'{planet.number}-{x}' for x in get_moon_letters(planet))
    return suffixes


def get_moon_letters(planet):
    return [helpers.to_letter(x + 1) for x in range(len(planet.moons))]


class Mode:
    def __init__(self):
        pass

    def handle_event(self, event):
        raise NotImplementedError

    def update(self, pressed_keys, dt):
        raise NotImplementedError


class SpaceMode(Mode, metaclass=ABCMeta):
    def __init__(self, scale, space, space_map, autopilot_text):
        super().__init__()
        game.screen.background_color = space.color
        self.background_sprites = set()
        self.minimap_background_sprites = set()
        self.npc_ships = set()
        self.npc_ships_remove = set()

        self.scale = scale
        self.space = space
        self.space_map = space_map
        self.player_ship = None
        self.reset_player()
        self.minimap = False
        self.paused = False
        self.can_collide = False

        self.autopilot_text = autopilot_text
        self.autopilot_target = None
        self.searching = False
        self.search_text = ''
        self.search_text_color = (255, 255, 255)

        if game.start:
            self.paused = True
            game.start = False

    def reset_player(self):
        self.player_ship = game.instance.player.get_ship(self.scale, self.space)
        self.can_collide = False

    def set_autopilot_target(self):
        raise NotImplementedError

    def get_search_autocomplete(self):
        text = self.search_text
        auto = helpers.auto_complete(text, data.system_search_names)
        if not auto:
            system_name = helpers.contained_prefix(text, game.instance.player.visited_systems)
            if system_name:
                system = data.systems.get(system_name.title())
                planet_names = get_planet_search_names(system)
                auto = helpers.auto_complete(text, planet_names)
                if not auto:
                    planet_name = helpers.contained_prefix(text, planet_names)
                    if planet_name:
                        planet_number = get_planet_number(system_name, planet_name)
                        moon_names = get_moon_search_names(system.planets[planet_number - 1])
                        auto = helpers.auto_complete(text, moon_names)
        return auto

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_F1:
                if not self.searching:
                    self.paused = not self.paused
            elif event.key == pg.K_F6:
                if not self.paused or self.searching:
                    self.paused = self.searching = not self.searching
                    self.search_text = ''
                    self.search_text_color = (255, 255, 255)
            elif event.key == pg.K_m:
                if not self.paused and not self.searching:
                    self.minimap = not self.minimap
            elif self.searching:
                if event.key == pg.K_RETURN:
                    auto_text = self.get_search_autocomplete()
                    self.autopilot_text = search_convert(auto_text)
                    if self.autopilot_text == search_convert(self.search_text):
                        self.set_autopilot_target()
                        if self.autopilot_target is not None:
                            self.paused = self.searching = False
                    else:
                        self.search_text = auto_text.upper()
                else:
                    auto_complete = False
                    if event.key == pg.K_ESCAPE:
                        self.paused = self.searching = False
                    elif event.key == pg.K_BACKSPACE:
                        self.search_text = self.search_text[:-1]
                    elif event.key == pg.K_DELETE:
                        self.search_text = ''
                    elif event.key == pg.K_TAB:
                        auto_complete = True
                    else:
                        key_text = event.unicode
                        if helpers.is_text(key_text):
                            self.search_text += key_text.upper()

                    self.search_text = helpers.single_spaces(self.search_text, False, True)
                    auto_text = self.get_search_autocomplete()
                    if auto_text:
                        self.search_text_color = (255, 255, 255)
                        if auto_complete:
                            self.search_text = auto_text.upper()
                    else:
                        self.search_text_color = (255, 0, 0)
            elif not self.paused:
                if event.key == pg.K_p:
                    self.autopilot_text = '#p'
                    self.set_autopilot_target()
                else:
                    self.autopilot_text = ''
                    self.autopilot_target = None

        return self

    def update_search(self, camera):
        if self.paused and not self.searching:
            game.pause_sprite.draw(camera)
        elif self.searching:
            game.search_sprite.draw(camera)
            text_surf = game.search_font.render(self.search_text, True, self.search_text_color)
            display_rect = game.screen.display_rect
            text_rect = text_surf.get_rect(centerx=display_rect.centerx, centery=display_rect.centery + 4)
            game.screen.draw(text_surf, text_rect)


class TrueSpaceMode(SpaceMode, metaclass=ABCMeta):
    def __init__(self, scale, space_map, autopilot_text):
        super().__init__(scale, spaces.truespace, space_map, autopilot_text)


class SolarSystemMode(TrueSpaceMode):
    def __init__(self, system, autopilot_text):
        system_map = SolarSystemMap(system, game.instance.time) if type(system) is str else system
        super().__init__(system_map.scale, system_map, autopilot_text)
        self.system = system_map.system
        random.seed(helpers.deterministic_hash(self.system.name))
        self.system_added = False
        sqrt_scale = math.sqrt(self.scale)
        for _ in range(int(200.0 / sqrt_scale)):
            bg_scale = 0.2 * sqrt_scale * (1.0 + random.random())
            bg_dist = max(1.0, 2.0 * (1.0 + random.random()))
            self.background_sprites.add(backgrounds.random_truespace_background_star(bg_scale, bg_dist / self.scale))
            self.minimap_background_sprites.add(backgrounds.random_truespace_minimap_background_star(0.5 * bg_scale))
        self.fade = Fade(self.space.color, 1.0 / sqrt_scale)
        self.set_autopilot_target()
        game.clock.tick()

    def get_autopilot_natural_orbiting_element(self, obj):
        for elem in self.space_map.elems:
            if isinstance(elem, NaturalOrbitingElement) and elem.name == obj.name:
                return elem
        return DummyTarget(obj.name) if helpers.contained_prefix(obj.name, data.systems.keys()) else None

    def set_autopilot_target(self):
        text = self.autopilot_text
        system_name = helpers.contained_prefix(text, data.systems.keys())
        system = data.systems.get(system_name)
        if system is not None:
            planet_name = helpers.contained_prefix(text, get_planet_names(system))
            if planet_name:
                planet_number = get_planet_number(system_name, planet_name)
                planet = system.planets[planet_number - 1] if 1 <= planet_number <= len(system.planets) else None
                if planet is not None:
                    self.autopilot_target = self.get_autopilot_natural_orbiting_element(planet)
                    return
            self.autopilot_target = system
            return
        self.autopilot_target = None

    def get_search_autocomplete(self):
        prefix = ''
        auto = super().get_search_autocomplete()
        if not auto:
            prefix = f'{self.system.name.upper()} '
            text = self.search_text
            planet_suffixes = get_planet_search_suffixes(self.system)
            auto = helpers.auto_complete(text, planet_suffixes)
            if not auto:
                planet_suffix = helpers.contained_prefix(text, planet_suffixes)
                if planet_suffix:
                    planet_number = int(planet_suffix) if planet_suffix.isnumeric() else helpers.roman_numeral_inv_map[planet_suffix]
                    moon_suffixes = get_moon_search_suffixes(self.system.planets[planet_number - 1])
                    auto = helpers.auto_complete(text, moon_suffixes)
        return f'{prefix}{auto}' if auto else auto

    def handle_event(self, event):
        return super().handle_event(event)

    def update(self, pressed_keys, dt):
        if not self.system_added:
            game.instance.player.visited_systems.add(self.system.name.upper())
            self.system_added = True

        if self.autopilot_target is not None and self.system.name == self.autopilot_target.name:
            self.autopilot_text = ''
            self.autopilot_target = None

        screen = game.screen
        h_width, h_height = self.space_map.half_width, self.space_map.half_height
        border_x, border_y = 0.0, 0.0
        ship = self.player_ship

        if not self.paused:
            ship_half_size = 0.5 * max(ship.rect.w, ship.rect.h)
            border_x = h_width + 0.5 * screen.display_width + ship_half_size
            border_y = h_height + 0.5 * screen.display_height + ship_half_size
            autopilot_pos = None
            if self.autopilot_target is not None:
                if isinstance(self.autopilot_target, NaturalOrbitingElement):
                    autopilot_pos = self.autopilot_target.sprite.pos
                else:
                    vertical = border_x - abs(ship.pos[0]) > border_y - abs(ship.pos[1])
                    target_x, target_y = 1.0e6 * border_x, 1.0e6 * border_y
                    autopilot_pos = np.array([
                        ship.pos[0] if vertical else (target_x if ship.pos[0] > 0.0 else -target_x),
                        (target_y if ship.pos[1] > 0.0 else -target_y) if vertical else ship.pos[1],
                    ])
            ship.update(pressed_keys, autopilot_pos, dt)

        padded_pos = np.clip(ship.pos, [-h_width, -h_height], [h_width, h_height])
        camera = padded_pos - 0.5 * screen.display_size

        screen.refresh()

        for sprite in self.background_sprites:
            sprite.draw(camera)

        for elem in self.space_map.elems:
            elem.draw(camera, self.minimap, self.paused)

        for sprite in self.npc_ships:
            sprite.draw(camera)

        ship.draw(camera)

        if self.minimap:
            corner_color = np.multiply(0.5, np.add((127, 127, 127), self.space.color))
            edge_color = np.multiply(1.2, corner_color), np.multiply(0.8, corner_color)
            minimap_rect = screen.minimap_rect
            border = screen.minimap_border
            pg.draw.rect(screen.display, corner_color, minimap_rect.move(-border, border))
            pg.draw.rect(screen.display, corner_color, minimap_rect.move(border, -border))
            pg.draw.rect(screen.display, edge_color[0], minimap_rect.move(-border, -border))
            pg.draw.rect(screen.display, edge_color[1], minimap_rect.move(border, border))
            pg.draw.rect(screen.display, self.space.color, screen.minimap_rect)

            for sprite in self.minimap_background_sprites:
                sprite.draw(camera)

            for elem in self.space_map.elems:
                elem.minimap_draw(camera, self.paused)

            for sprite in self.npc_ships:
                sprite.minimap_draw(self.space_map.minimap_scale)

            ship.minimap_draw(self.space_map.minimap_scale)

        if not self.paused:
            off_cam_x = abs(ship.pos[0]) > border_x
            off_cam_y = abs(ship.pos[1]) > border_y
            if off_cam_x or off_cam_y:
                pos = helpers.coords_to_pos(self.space_map.system.coords)
                game.instance.player.set_pos_vel(pos, np.zeros(2), ship.angle, 0.0)
                new_mode = HyperSpaceMode(self.autopilot_text)
                # new_target = new_mode.autopilot_target
                # if new_target is not None:
                # diff = helpers.coords_to_pos(new_target.coords) - pos
                # game.instance.player.angle = new_mode.player_ship.angle = np.arctan2(diff[1], diff[0])
                return new_mode

            collision = False
            for elem in self.space_map.elems:
                if pg.sprite.collide_circle(ship, elem.sprite):
                    collision = True
                    if isinstance(elem, NaturalOrbitingElement) and\
                            (self.can_collide if self.autopilot_target is None else self.autopilot_target == elem):
                        cos, sin = math.cos(ship.angle), math.sin(ship.angle)
                        b = abs(cos) > abs(sin)
                        mult_x, mult_y = np.sign(cos) if b else cos, sin if b else np.sign(sin)
                        system_map = PlanetarySystemMap(self.system, elem.planet, game.instance.time)
                        pos_x, pos_y = -system_map.half_width * mult_x, -system_map.half_height * mult_y
                        self.player_ship = None
                        game.instance.player.set_pos_vel(np.array([pos_x, pos_y]), np.zeros(2), ship.angle, 0.0)
                        new_mode = PlanetarySystemMode(self, system_map, elem.sprite.pos.copy(), self.autopilot_text)
                        new_target = new_mode.autopilot_target
                        if isinstance(new_target, NaturalOrbitingElement) and new_target.orbit_angle is not None:
                            angle = helpers.positive_fmod(math.pi + new_target.orbit_angle, constants.two_pi)
                            cos, sin = math.cos(angle), math.sin(angle)
                            b = abs(cos) > abs(sin)
                            mult_x, mult_y = np.sign(cos) if b else cos, sin if b else np.sign(sin)
                            pos_x, pos_y = -system_map.half_width * mult_x, -system_map.half_height * mult_y
                            game.instance.player.pos = new_mode.player_ship.pos = np.array([pos_x, pos_y])
                            game.instance.player.angle = new_mode.player_ship.angle = angle
                        return new_mode

            if not collision:
                self.can_collide = True

        self.fade.update(dt)

        self.update_search(camera)

        return self


class PlanetarySystemMode(TrueSpaceMode):
    def __init__(self, solar_system, planet_info, system_planet_pos, autopilot_text):
        self.solar_system_mode = SolarSystemMode(solar_system, autopilot_text) if type(solar_system) is str else solar_system
        self.solar_system_map = self.solar_system_mode.space_map
        self.solar_system = self.solar_system_map.system
        if type(planet_info) is int:
            self.planet = self.solar_system.planets[planet_info - 1]
            planetary_system_map = PlanetarySystemMap(self.solar_system, self.planet, game.instance.time)
        else:
            self.planet = planet_info.planet
            planetary_system_map = planet_info
        super().__init__(planetary_system_map.scale, planetary_system_map, autopilot_text)
        self.system_planet_pos = system_planet_pos
        self.background_sprites = self.solar_system_mode.background_sprites
        self.fade = Fade(self.space.color, 1.0)
        self.set_autopilot_target()
        game.clock.tick()

    def get_autopilot_natural_orbiting_element(self, obj):
        for elem in self.space_map.elems:
            if isinstance(elem, NaturalOrbitingElement) and elem.name == obj.name:
                return elem
        return DummyTarget(obj.name) if helpers.contained_prefix(obj.name, data.systems.keys()) else None

    def set_autopilot_target(self):
        text = self.autopilot_text
        if text == '#p':
            self.autopilot_target = DummyTarget(self.planet.name)
            return
        system_name = helpers.contained_prefix(text, data.systems.keys())
        system = data.systems.get(system_name)
        if system is not None:
            planet_name = helpers.contained_prefix(text, get_planet_names(system))
            if planet_name:
                planet_number = get_planet_number(system_name, planet_name)
                planet = system.planets[planet_number - 1] if 1 <= planet_number <= len(system.planets) else None
                if planet is not None:
                    moon_name = helpers.contained_prefix(text, get_moon_names(planet))
                    if moon_name:
                        moon_number = ord(moon_name[-1]) - 64
                        moon = planet.moons[moon_number - 1] if 1 <= moon_number <= len(planet.moons) else None
                        if moon is not None:
                            self.autopilot_target = self.get_autopilot_natural_orbiting_element(moon)
                            return
                    self.autopilot_target = self.get_autopilot_natural_orbiting_element(planet)
                    return
            self.autopilot_target = system
            return
        self.autopilot_target = None

    def get_search_autocomplete(self):
        prefix = ''
        auto = super().get_search_autocomplete()
        if not auto:
            prefix = f'{self.solar_system.name.upper()} '
            text = self.search_text
            planet_suffixes = get_planet_search_suffixes(self.solar_system)
            auto = helpers.auto_complete(text, planet_suffixes)
            if not auto:
                planet_suffix = helpers.contained_prefix(text, planet_suffixes)
                if planet_suffix:
                    planet_number = int(planet_suffix) if planet_suffix.isnumeric() else helpers.roman_numeral_inv_map[planet_suffix]
                    planet = self.solar_system.planets[planet_number - 1]
                    moon_suffixes = get_moon_search_suffixes(planet)
                    auto = helpers.auto_complete(text, moon_suffixes)
                    if not auto:
                        prefix = f'{prefix}{helpers.roman_numeral_map[self.planet.number]}-'
                        auto = helpers.auto_complete(text, get_moon_letters(planet))
        return f'{prefix}{auto}' if auto else auto

    def handle_event(self, event):
        return super().handle_event(event)

    def update(self, pressed_keys, dt):
        if self.autopilot_target is not None:
            if self.solar_system.name == self.autopilot_target.name or\
                    (self.planet.name == self.autopilot_target.name and type(self.autopilot_target) is not DummyTarget):
                self.autopilot_text = ''
                self.autopilot_target = None

        h_width, h_height = self.space_map.half_width, self.space_map.half_height
        border_x, border_y = 0.0, 0.0
        ship = self.player_ship

        if not self.paused:
            ship_half_size = 0.5 * max(ship.rect.w, ship.rect.h)
            border_x = h_width + ship_half_size
            border_y = h_height + ship_half_size
            autopilot_pos = None
            if self.autopilot_target is not None:
                if isinstance(self.autopilot_target, NaturalOrbitingElement):
                    autopilot_pos = self.autopilot_target.sprite.pos
                elif self.autopilot_target.name == self.planet.name:
                    autopilot_pos = np.zeros(2)
                else:
                    vertical = border_x - abs(ship.pos[0]) > border_y - abs(ship.pos[1])
                    target_x, target_y = 1.0e3 * border_x, 1.0e3 * border_y
                    autopilot_pos = np.array([
                        ship.pos[0] if vertical else (target_x if ship.pos[0] > 0.0 else -target_x),
                        (target_y if ship.pos[1] > 0.0 else -target_y) if vertical else ship.pos[1],
                    ])
            ship.update(pressed_keys, autopilot_pos, dt)

        # padded_pos = np.clip(ship.pos, [-h_width, -h_height], [h_width, h_height])
        # camera = padded_pos - 0.5 * game.screen.display_size
        camera = -0.5 * game.screen.display_size

        game.screen.refresh()

        for sprite in self.background_sprites:
            sprite.draw(camera)

        for elem in self.space_map.elems:
            elem.draw(camera, self.minimap, self.paused)

        for sprite in self.npc_ships:
            sprite.draw(camera)

        self.player_ship.draw(camera)

        if not self.paused:
            off_cam_x = abs(ship.pos[0]) > border_x
            off_cam_y = abs(ship.pos[1]) > border_y
            if off_cam_x or off_cam_y:
                game.instance.player.set_pos_vel(self.system_planet_pos.copy(), np.zeros(2), ship.angle, 0.0)
                self.solar_system_mode.reset_player()
                self.solar_system_mode.autopilot_text = self.autopilot_text
                self.solar_system_mode.set_autopilot_target()
                self.solar_system_mode.fade.counter = 0.0
                return self.solar_system_mode

            collision = False
            for elem in self.space_map.elems:
                if pg.sprite.collide_circle(self.player_ship, elem.sprite):
                    collision = True
                    if isinstance(elem, NaturalOrbitingElement) and \
                            (self.can_collide if self.autopilot_target is None else self.autopilot_target.name == elem.sprite.name):
                        self.paused = True
                        self.autopilot_text = ''
                        self.autopilot_target = None
                        self.can_collide = False
                        ship.pos = elem.sprite.pos.copy()
                        ship.vel = np.zeros(2)
                        ship.ang_vel = 0.0
                        game.instance.player.set_pos_vel(ship.pos, ship.vel, ship.angle, ship.ang_vel)
                        break

            if not collision:
                self.can_collide = True

        self.fade.update(dt)

        self.update_search(camera)

        return self


class HyperSpaceMode(SpaceMode):
    def __init__(self, autopilot_text):
        super().__init__(1.0, spaces.hyperspace, HyperSpaceMap(), autopilot_text)
        random.seed(hash(game.instance))
        for _ in range(200):
            bg_scale = 0.25 * (1.0 + random.random())
            bg_dist = 0.5 * (1.0 + random.random())
            bg_star = backgrounds.random_hyperspace_background_star(bg_scale, bg_dist / self.scale)
            self.background_sprites.add(bg_star)
        self.set_autopilot_target()
        game.clock.tick()

    def set_autopilot_target(self):
        self.autopilot_target = data.systems.get(helpers.contained_prefix(self.autopilot_text, data.systems.keys()))

    def get_search_autocomplete(self):
        return super().get_search_autocomplete()

    def handle_event(self, event):
        return super().handle_event(event)

    def spawn_npc_ship(self):
        ship_pos = self.player_ship.pos
        for race in helpers.each(data.race_list, random.randrange(0, len(data.race_list))):
            if np.linalg.norm(ship_pos - race.soi_pos) < race.soi_radius:
                image = race.get_ship_image(self.space)
                offset = random.uniform(0.0, constants.two_pi)
                pos = ship_pos + game.screen.display_max_dim * np.array([math.cos(offset), math.sin(offset)])
                ship_data = data.ships[race.ship_name]
                thrust, ang_thrust = ship_data.thrust, ship_data.ang_thrust
                engine = NPCEngine(0.8 * thrust, 0.1 * thrust, 0.1 * thrust, ang_thrust, 0.05, 0.05)
                vel = np.zeros(2)
                angle = random.uniform(0.0, constants.two_pi)
                ship = InterceptShip(image, self.scale, pos, self.space, engine, ship_data.mass, ship_data.moi, ship_data.area, vel, angle, 0.0, race.is_ally())
                self.npc_ships.add(ship)
                break

    def update(self, pressed_keys, dt):
        ship = self.player_ship
        if not self.paused:
            autopilot_pos = None if self.autopilot_target is None else helpers.coords_to_pos(self.autopilot_target.coords)
            ship.update(pressed_keys, autopilot_pos, dt)

        camera = ship.pos - 0.5 * game.screen.display_size

        game.screen.refresh()

        if not self.paused and random.random() < 0.1 * dt:
            # self.spawn_npc_ship()
            pass

        for sprite in self.background_sprites:
            sprite.draw(camera)

        for elem in self.space_map.elems:
            elem.draw(camera, self.minimap, self.paused)

        if not self.paused:
            removed = set()

            for sprite in self.npc_ships:
                sprite.update(None, ship.pos, dt)
                if np.linalg.norm(ship.pos - sprite.pos) > 2.0 * game.screen.display_max_dim:
                    removed.add(sprite)

            for sprite in removed:
                self.npc_ships.remove(sprite)

        for sprite in self.npc_ships:
            sprite.draw(camera)

        ship.draw(camera)

        if not self.paused:
            for npc_ship in self.npc_ships_remove:
                self.npc_ships.remove(npc_ship)
            self.npc_ships_remove.clear()

            collision = False
            for elem in self.space_map.elems:
                if pg.sprite.collide_circle(ship, elem.sprite):
                    collision = True
                    if isinstance(elem, HyperSpaceSystemElement) and\
                            (self.can_collide if self.autopilot_target is None else self.autopilot_target.name == elem.name):
                        angle = ship.angle
                        cos, sin = math.cos(angle), math.sin(angle)
                        b = abs(cos) > abs(sin)
                        mult_x, mult_y = np.sign(cos) if b else cos, sin if b else np.sign(sin)
                        system_map = SolarSystemMap(elem.name, game.instance.time)
                        pos_x = -(system_map.half_width + 0.25 * game.screen.display_width) * mult_x
                        pos_y = -(system_map.half_height + 0.25 * game.screen.display_height) * mult_y
                        game.instance.player.set_pos_vel(np.array([pos_x, pos_y]), np.zeros(2), angle, 0.0)
                        new_mode = SolarSystemMode(system_map, self.autopilot_text)
                        new_target = new_mode.autopilot_target
                        if isinstance(new_target, NaturalOrbitingElement) and new_target.orbit_angle is not None:
                            angle = helpers.positive_fmod(math.pi + new_target.orbit_angle, constants.two_pi)
                            cos, sin = math.cos(angle), math.sin(angle)
                            b = abs(cos) > abs(sin)
                            mult_x, mult_y = np.sign(cos) if b else cos, sin if b else np.sign(sin)
                            pos_x = -(system_map.half_width + 0.25 * game.screen.display_width) * mult_x
                            pos_y = -(system_map.half_height + 0.25 * game.screen.display_height) * mult_y
                            game.instance.player.pos = new_mode.player_ship.pos = np.array([pos_x, pos_y])
                            game.instance.player.angle = new_mode.player_ship.angle = angle
                        return new_mode

            for npc_ship in self.npc_ships:
                if pg.sprite.collide_rect(ship, npc_ship):
                    player_mask = pg.mask.from_surface(ship.image)
                    npc_mask = pg.mask.from_surface(npc_ship.image)
                    if player_mask.overlap(npc_mask, npc_ship.pos - ship.pos):
                        collision = True
                        if self.can_collide:
                            self.paused = True
                            self.can_collide = False
                            ship.vel = np.zeros(2)
                            ship.ang_vel = 0.0
                            game.instance.player.set_pos_vel(ship.pos, ship.vel, ship.angle, ship.ang_vel)
                            self.npc_ships_remove.add(npc_ship)
                            break

            if not collision:
                self.can_collide = True

        # self.fade.update(dt)

        self.update_search(camera)

        return self
