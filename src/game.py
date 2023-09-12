import os

import numpy as np
import pygame as pg

import data
import helpers

from pygame import Rect
from pygame.font import SysFont
from pygame.time import Clock
from modes import HyperSpaceMode, SolarSystemMode, PlanetarySystemMode
from player import Player
from sprites import Sprite, HUDSprite


class Screen:
    def __init__(self):
        self.display = pg.display.set_mode((0, 0))
        self.display_rect = self.display.get_rect()
        self.display_width = float(self.display.get_width())
        self.display_height = float(self.display.get_height())
        self.display_size = np.array([self.display_width, self.display_height])
        self.display_min_dim = min(self.display_width, self.display_height)
        self.display_max_dim = max(self.display_width, self.display_height)
        self.display_min_dim_index = 1 if self.display_min_dim == self.display_height else 0
        self.display_max_dim_index = 1 if self.display_max_dim == self.display_height else 0

        self.background_color = (0, 0, 0)

        self.minimap_size_mult = 0.375
        self.minimap_center = 0.5 * self.display_size
        self.minimap_half_size = self.minimap_size_mult * self.display_size
        self.minimap_rect = Rect(self.minimap_center - self.minimap_half_size, 2.0 * self.minimap_half_size)
        self.minimap_border = 0.015625 * self.display_min_dim

    def refresh(self):
        self.display.fill(self.background_color)

    def draw(self, source, dest):
        self.display.blit(source, dest)


class Game:
    def __init__(self):
        self.name = None
        self.player = None
        self.time = None
        self.mode = None


start = True
clock: Clock
screen: Screen
instance = Game()

pause_sprite: Sprite
search_sprite: Sprite
search_font: SysFont


def loop():
    while 1:
        dt = 0.001 * max(1, clock.tick())
        for event in pg.event.get():
            if event.type == pg.QUIT:
                save_game()
                return
            else:
                instance.mode = instance.mode.handle_event(event)

        pressed_keys = pg.key.get_pressed()
        instance.mode = instance.mode.update(pressed_keys, dt)

        pg.display.flip()


def load_game(name):
    instance.name = name

    player = Player()
    instance.player = player

    def read_thrusters(line):
        t = []
        for s in line.split(';;'):
            s = s.strip()
            if s:
                parts = s.split('..')
                for _ in range(int(parts[0])):
                    t.append(data.thrusters[parts[1]])
        return t

    try:
        with open(f'../saves/{name}.txt') as file:
            lines = [line.rstrip() for line in file.readlines()]

            player.ship_name = lines[0]

            player.engine.set_thrusters(read_thrusters(lines[1]))
            player.engine.set_damp_factors(*(float(x) for x in lines[2].split(';;')))

            pos = np.array([float(x) for x in lines[3].split(';;')])
            vel = np.array([float(x) for x in lines[4].split(';;')])
            angle = float(lines[5])
            ang_vel = float(lines[6])
            player.set_pos_vel(pos, vel, angle, ang_vel)

            instance.time = int(lines[7])

            mode_data = lines[8].split(';;')
            if mode_data[0] == 'solar_system':
                instance.mode = SolarSystemMode(mode_data[1], '')
            elif mode_data[0] == 'planetary_system':
                planet_pos = np.array([float(x) for x in mode_data[3].split('&&')])
                instance.mode = PlanetarySystemMode(mode_data[1], int(mode_data[2]), planet_pos, '')
            elif mode_data[0] == 'hyperspace':
                instance.mode = HyperSpaceMode('')

            player.visited_systems = {x for x in lines[9].split(';;')}

    except EnvironmentError:
        player.ship_name = 'Cruiser'

        thrusters = read_thrusters('16..Thermonuclear Thruster;;'
                                   '2..Thermonuclear Retro-Thruster;;'
                                   '2..Thermonuclear Lateral Stabiliser;;'
                                   '12..Thermonuclear Turning Jet')
        player.engine.set_thrusters(thrusters)
        player.engine.set_damp_factors(0.05, 0.05)

        player.set_pos_vel(np.array([0.0, 0.0]), np.zeros(2), 0.0, 0.0)

        instance.time = 0

        instance.mode = SolarSystemMode('Sol', '')

        player.visited_systems = {'SOL'}


def save_game():
    if not os.path.exists('../saves'):
        os.makedirs('../saves')

    def thrusters_str(t):
        return ';;'.join(f'{v}..{k.name}' for (k, v) in helpers.quantity_dict(t).items())

    def known_systems_str(s):
        return ';;'.join(s)

    with open(f'../saves/{instance.name}.txt', 'w') as file:
        player = instance.player
        file.write(f'{player.ship_name}\n')

        file.write(f'{thrusters_str(player.engine.thrusters)}\n')
        file.write(f'{player.engine.damp_factor};;{player.engine.ang_damp_factor}\n')

        file.write(f'{player.pos[0]};;{player.pos[1]}\n')
        file.write(f'{player.vel[0]};;{player.vel[1]}\n')
        file.write(f'{player.angle}\n')
        file.write(f'{player.ang_vel}\n')

        file.write(f'{instance.time}\n')

        mode = instance.mode
        if type(mode) is SolarSystemMode:
            file.write(f'solar_system;;{mode.system.name}\n')
        elif type(mode) is PlanetarySystemMode:
            planet_pos = f'{mode.system_planet_pos[0]}&&{mode.system_planet_pos[1]}'
            file.write(f'planetary_system;;{mode.solar_system.name};;{mode.planet.number};;{planet_pos}\n')
        elif type(mode) is HyperSpaceMode:
            file.write(f'hyperspace\n')

        file.write(f'{known_systems_str(player.visited_systems)}\n')


def init():
    global clock, screen, pause_sprite, search_sprite, search_font
    clock = pg.time.Clock()
    screen = Screen()
    pause_sprite = HUDSprite('../assets/images/pause.png', 1.0, screen.display_rect.center)
    search_sprite = HUDSprite('../assets/images/search.png', 1.0, screen.display_rect.center)
    search_font = pg.font.SysFont('Consolas', 52)
    load_game('game')
